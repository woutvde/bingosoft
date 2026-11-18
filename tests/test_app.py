import os
import re
import tempfile
import time
import unittest

os.environ['BINGO_DATA_FILE'] = os.path.join(
    tempfile.mkdtemp(prefix='bingo-test-'), 'test_data.json'
)

import app as bingo  # noqa: E402


class BingoApiTest(unittest.TestCase):
    def setUp(self):
        self.client = bingo.app.test_client()
        with bingo.storage.lock:
            bingo.storage.games.clear()
            bingo.storage.pending_displays.clear()
            bingo.storage.display_to_game.clear()
            bingo.storage.save()

    def create_game(self):
        res = self.client.post('/api/create_game')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertRegex(data['game_code'], r'^[A-Z]{4}$')
        self.assertTrue(data['token'])
        return data['game_code'], data['token']

    def open_display(self):
        res = self.client.get('/display')
        self.assertEqual(res.status_code, 200)
        match = re.search(r'const displayCode = "([A-Z]{4})"', res.get_data(as_text=True))
        self.assertIsNotNone(match)
        return match.group(1)

    def post_json(self, url, payload):
        return self.client.post(url, json=payload)

    def test_health(self):
        res = self.client.get('/health')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json(), {"status": "ok"})

    def test_create_and_join_game(self):
        game_code, token = self.create_game()
        res = self.post_json(f'/api/join_game/{game_code.lower()}', {})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()['token'], token)

    def test_join_unknown_game_returns_404(self):
        res = self.post_json('/api/join_game/ZZZZ', {})
        self.assertEqual(res.status_code, 404)

    def test_heartbeat_requires_valid_token(self):
        game_code, token = self.create_game()
        res = self.post_json(f'/api/heartbeat/{game_code}', {'token': 'wrong'})
        self.assertEqual(res.status_code, 401)
        res = self.post_json(f'/api/heartbeat/{game_code}', {'token': token})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json(), {"status": "alive"})

    def test_action_requires_valid_token(self):
        game_code, _ = self.create_game()
        res = self.post_json(f'/api/action/{game_code}', {'action': 'call', 'number': 5, 'token': 'wrong'})
        self.assertEqual(res.status_code, 401)

    def test_call_undo_reset(self):
        game_code, token = self.create_game()
        res = self.post_json(f'/api/action/{game_code}', {'action': 'call', 'number': 5, 'token': token})
        self.assertEqual(res.status_code, 200)
        # Dubbel en ongeldig getal worden genegeerd
        self.post_json(f'/api/action/{game_code}', {'action': 'call', 'number': 5, 'token': token})
        self.post_json(f'/api/action/{game_code}', {'action': 'call', 'number': 91, 'token': token})
        self.post_json(f'/api/action/{game_code}', {'action': 'call', 'number': 'abc', 'token': token})
        state = self.client.get(f'/api/operator_state/{game_code}').get_json()
        self.assertEqual(state['called_numbers'], [5])

        self.post_json(f'/api/action/{game_code}', {'action': 'call', 'number': 42, 'token': token})
        self.post_json(f'/api/action/{game_code}', {'action': 'undo', 'token': token})
        state = self.client.get(f'/api/operator_state/{game_code}').get_json()
        self.assertEqual(state['called_numbers'], [5])

        self.post_json(f'/api/action/{game_code}', {'action': 'reset', 'token': token})
        state = self.client.get(f'/api/operator_state/{game_code}').get_json()
        self.assertEqual(state['called_numbers'], [])

    def test_set_display_theme(self):
        game_code, token = self.create_game()
        res = self.post_json(f'/api/action/{game_code}', {'action': 'set_display_theme', 'theme': 'light', 'token': token})
        self.assertEqual(res.get_json()['display_theme'], 'light')
        res = self.post_json(f'/api/action/{game_code}', {'action': 'set_display_theme', 'theme': 'neon', 'token': token})
        self.assertEqual(res.get_json(), {"status": "success"})
        state = self.client.get(f'/api/operator_state/{game_code}').get_json()
        self.assertEqual(state['display_theme'], 'light')

    def test_display_link_state_unlink_flow(self):
        game_code, token = self.create_game()
        display_code = self.open_display()

        state = self.client.get(f'/api/state/{display_code}').get_json()
        self.assertFalse(state['operator_connected'])

        res = self.post_json(f'/api/link_display/{game_code}', {'token': token, 'display_code': display_code.lower()})
        self.assertEqual(res.status_code, 200)

        self.post_json(f'/api/action/{game_code}', {'action': 'call', 'number': 17, 'token': token})
        state = self.client.get(f'/api/state/{display_code}').get_json()
        self.assertTrue(state['operator_connected'])
        self.assertEqual(state['last_number'], 17)
        self.assertEqual(state['previous_numbers'], [17])

        res = self.post_json(f'/api/unlink_display/{game_code}', {'token': token, 'display_code': display_code})
        self.assertEqual(res.status_code, 200)
        state = self.client.get(f'/api/state/{display_code}').get_json()
        self.assertFalse(state['operator_connected'])

    def test_link_invalid_display_code_returns_400(self):
        game_code, token = self.create_game()
        res = self.post_json(f'/api/link_display/{game_code}', {'token': token, 'display_code': 'ZZZZ'})
        self.assertEqual(res.status_code, 400)

    def test_link_display_requires_token(self):
        game_code, _ = self.create_game()
        display_code = self.open_display()
        res = self.post_json(f'/api/link_display/{game_code}', {'token': 'wrong', 'display_code': display_code})
        self.assertEqual(res.status_code, 401)

    def test_auto_link(self):
        game_code, _ = self.create_game()
        res = self.client.get(f'/display/auto_link/{game_code}')
        self.assertEqual(res.status_code, 200)
        match = re.search(r'const displayCode = "([A-Z]{4})"', res.get_data(as_text=True))
        display_code = match.group(1)
        state = self.client.get(f'/api/state/{display_code}').get_json()
        self.assertTrue(state['operator_connected'])
        res = self.client.get('/display/auto_link/ZZZZ')
        self.assertEqual(res.status_code, 404)

    def test_disconnect_releases_displays(self):
        game_code, token = self.create_game()
        display_code = self.open_display()
        self.post_json(f'/api/link_display/{game_code}', {'token': token, 'display_code': display_code})

        res = self.post_json(f'/api/disconnect/{game_code}', {'token': token})
        self.assertEqual(res.get_json(), {"status": "disconnected"})
        self.assertEqual(self.client.get(f'/api/operator_state/{game_code}').status_code, 404)
        state = self.client.get(f'/api/state/{display_code}').get_json()
        self.assertFalse(state['operator_connected'])

    def test_error_messages_are_localized(self):
        res = self.post_json('/api/join_game/ZZZZ', {'lang': 'en'})
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.get_json()['error'], 'Game code not found')
        res = self.post_json('/api/join_game/ZZZZ', {'lang': 'de'})
        self.assertEqual(res.get_json()['error'], 'Spielcode nicht gefunden')
        res = self.post_json('/api/join_game/ZZZZ', {'lang': 'fr'})
        self.assertEqual(res.get_json()['error'], 'Code de partie introuvable')
        # Zonder lang-parameter blijft de standaardtaal (Nederlands) behouden
        res = self.post_json('/api/join_game/ZZZZ', {})
        self.assertEqual(res.get_json()['error'], 'Spelcode niet gevonden')
        # Onbekende taal valt terug op de standaardtaal
        res = self.post_json('/api/join_game/ZZZZ', {'lang': 'xx'})
        self.assertEqual(res.get_json()['error'], 'Spelcode niet gevonden')
        # Query string werkt ook
        res = self.client.post('/api/join_game/ZZZZ?lang=en')
        self.assertEqual(res.get_json()['error'], 'Game code not found')

    def test_i18n_static_file_is_served(self):
        res = self.client.get('/static/i18n.js')
        self.assertEqual(res.status_code, 200)
        body = res.get_data(as_text=True)
        for lang in ('en', 'nl', 'de', 'fr'):
            self.assertIn(f"{lang}: {{", body)
        self.assertIn('SUPPORTED_LANGS', body)

    def test_non_json_body_does_not_crash(self):
        game_code, _ = self.create_game()
        res = self.client.post(
            f'/api/heartbeat/{game_code}',
            data='dit is geen json',
            content_type='text/plain',
        )
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.get_json(), {"error": "Niet geautoriseerd"})

    def test_cleanup_stale_games(self):
        game_code, token = self.create_game()
        display_code = self.open_display()
        self.post_json(f'/api/link_display/{game_code}', {'token': token, 'display_code': display_code})

        with bingo.storage.lock:
            bingo.storage.games[game_code].last_active = time.time() - bingo.STALE_TIMEOUT - 1
        stale = bingo.cleanup_stale_games()
        self.assertIn(game_code, stale)
        with bingo.storage.lock:
            self.assertNotIn(game_code, bingo.storage.games)
            self.assertIn(display_code, bingo.storage.pending_displays)
            self.assertNotIn(display_code, bingo.storage.display_to_game)

    def test_storage_persists_to_disk(self):
        game_code, token = self.create_game()
        self.post_json(f'/api/action/{game_code}', {'action': 'call', 'number': 33, 'token': token})
        reloaded = bingo.Storage(bingo.DATA_FILE)
        self.assertIn(game_code, reloaded.games)
        self.assertEqual(reloaded.games[game_code].token, token)
        self.assertEqual(reloaded.games[game_code].called_numbers, [33])


if __name__ == '__main__':
    unittest.main()
