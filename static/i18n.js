const SUPPORTED_LANGS = ['en', 'nl', 'de', 'fr'];
const DEFAULT_LANG = 'nl';

const I18N = {
    en: {
        doc_title_operator: 'Bingo Operator Console',
        doc_title_display: 'Bingo Projection Screen',
        language: 'Language:',
        console: 'Console:',
        tv_screen: 'TV screen:',
        dark: 'Dark',
        light: 'Light',
        setup_heading: 'Bingo Operator Setup',
        setup_subtitle: 'Choose how you want to manage and start the bingo screens.',
        mode_local: 'Local Mode',
        mode_local_desc: 'Start directly and open the projection in a new window on this computer.',
        mode_wireless: 'Wireless Mode',
        mode_wireless_desc: 'Link multiple external devices (such as TVs or Raspberry Pis) wirelessly via code pairing.',
        mode_display: 'Use as Screen',
        mode_display_desc: 'Start this device as a passive TV receiver to display bingo numbers.',
        resume_divider: 'OR RESUME GAME SESSION',
        code_placeholder: 'CODE',
        resume_button: 'Resume Existing Game',
        game_code_label: 'Game code:',
        stop_game: 'Stop game',
        number_selection: 'Bingo Number Selection',
        undo: 'Undo Last',
        reset_board: 'Reset Board',
        linked_screens: 'Linked Screens',
        enter_display_code: 'Enter a display code to add an extra screen:',
        tv_code_placeholder: 'TV CODE',
        link_screen: 'Link Screen',
        no_screens: 'No active screens linked.',
        tv_code: 'TV Code:',
        err_invalid_code: 'Enter a valid code.',
        err_resume: 'Error resuming game.',
        err_network: 'Network error.',
        err_start_game: 'Could not start a game instance.',
        err_start_multi: 'Error creating multi-screen game.',
        err_display_code: 'Enter a 4-letter code.',
        err_failed: 'Failed',
        err_conn: 'Connection error.',
        session_expired: 'Session expired.',
        confirm_reset: 'Are you sure you want to reset all called numbers?',
        link_screen_title: 'Link Screen',
        link_instructions: 'Open the bingo console on your computer and enter the code above to start.',
        new_number: 'New Number',
        ready: 'Ready to start...',
        previous_numbers: 'Previous called numbers'
    },
    nl: {
        doc_title_operator: 'Bingo Operatorscherm',
        doc_title_display: 'Bingo Projectiescherm',
        language: 'Taal:',
        console: 'Console:',
        tv_screen: 'TV Scherm:',
        dark: 'Donker',
        light: 'Licht',
        setup_heading: 'Bingo Operator Setup',
        setup_subtitle: 'Kies hoe je de bingo schermen wilt beheren en opstarten.',
        mode_local: 'Lokale Modus',
        mode_local_desc: 'Start direct op en open de projectie in een nieuw venster op deze computer.',
        mode_wireless: 'Draadloze Modus',
        mode_wireless_desc: "Koppel meerdere externe apparaten (zoals TV's of Raspberry Pi's) draadloos via code koppelingen.",
        mode_display: 'Gebruik als Scherm',
        mode_display_desc: 'Start dit apparaat op als passieve TV-ontvanger om bingo-nummers te tonen.',
        resume_divider: 'OF SPEELSESSIE HERSTELLEN',
        code_placeholder: 'CODE',
        resume_button: 'Hervat Bestaand Spel',
        game_code_label: 'Spelcode:',
        stop_game: 'Spel stopzetten',
        number_selection: 'Bingo Nummer Selectie',
        undo: 'Laatste Herstellen',
        reset_board: 'Reset Kaart',
        linked_screens: 'Schermen Gekoppeld',
        enter_display_code: 'Voer display-code in om extra scherm toe te voegen:',
        tv_code_placeholder: 'TV CODE',
        link_screen: 'Koppel Scherm',
        no_screens: 'Geen actieve schermen gekoppeld.',
        tv_code: 'TV Code:',
        err_invalid_code: 'Voer een geldige code in.',
        err_resume: 'Fout bij hervatten.',
        err_network: 'Netwerkfout.',
        err_start_game: 'Kon geen game instantie starten.',
        err_start_multi: 'Fout bij aanmaken van multi-screen spel.',
        err_display_code: 'Voer een 4-letterige code in.',
        err_failed: 'Mislukt',
        err_conn: 'Verbindingsfout.',
        session_expired: 'Sessie verlopen.',
        confirm_reset: 'Weet je zeker dat je alle getrokken nummers wilt resetten?',
        link_screen_title: 'Scherm Koppelen',
        link_instructions: 'Open de bingo console op je computer en voer de bovenstaande code in om te starten.',
        new_number: 'Nieuw Nummer',
        ready: 'Klaar voor de start...',
        previous_numbers: 'Vorige getrokken nummers'
    },
    de: {
        doc_title_operator: 'Bingo-Bedienkonsole',
        doc_title_display: 'Bingo-Projektionsbildschirm',
        language: 'Sprache:',
        console: 'Konsole:',
        tv_screen: 'TV-Bildschirm:',
        dark: 'Dunkel',
        light: 'Hell',
        setup_heading: 'Bingo-Einrichtung',
        setup_subtitle: 'Wähle aus, wie du die Bingo-Bildschirme verwalten und starten möchtest.',
        mode_local: 'Lokaler Modus',
        mode_local_desc: 'Direkt starten und die Projektion in einem neuen Fenster auf diesem Computer öffnen.',
        mode_wireless: 'Drahtloser Modus',
        mode_wireless_desc: 'Mehrere externe Geräte (z. B. Fernseher oder Raspberry Pis) drahtlos per Code koppeln.',
        mode_display: 'Als Bildschirm verwenden',
        mode_display_desc: 'Dieses Gerät als passiven TV-Empfänger starten, um Bingo-Zahlen anzuzeigen.',
        resume_divider: 'ODER SPIELSITZUNG WIEDERHERSTELLEN',
        code_placeholder: 'CODE',
        resume_button: 'Bestehendes Spiel fortsetzen',
        game_code_label: 'Spielcode:',
        stop_game: 'Spiel stoppen',
        number_selection: 'Bingo-Zahlenauswahl',
        undo: 'Letztes rückgängig machen',
        reset_board: 'Brett zurücksetzen',
        linked_screens: 'Gekoppelte Bildschirme',
        enter_display_code: 'Display-Code eingeben, um einen weiteren Bildschirm hinzuzufügen:',
        tv_code_placeholder: 'TV-CODE',
        link_screen: 'Bildschirm koppeln',
        no_screens: 'Keine aktiven Bildschirme gekoppelt.',
        tv_code: 'TV-Code:',
        err_invalid_code: 'Gib einen gültigen Code ein.',
        err_resume: 'Fehler beim Wiederherstellen des Spiels.',
        err_network: 'Netzwerkfehler.',
        err_start_game: 'Spielinstanz konnte nicht gestartet werden.',
        err_start_multi: 'Fehler beim Erstellen des Multi-Screen-Spiels.',
        err_display_code: 'Gib einen Code mit 4 Buchstaben ein.',
        err_failed: 'Fehlgeschlagen',
        err_conn: 'Verbindungsfehler.',
        session_expired: 'Sitzung abgelaufen.',
        confirm_reset: 'Bist du sicher, dass du alle gezogenen Zahlen zurücksetzen möchtest?',
        link_screen_title: 'Bildschirm koppeln',
        link_instructions: 'Öffne die Bingo-Konsole auf deinem Computer und gib den obigen Code ein, um zu starten.',
        new_number: 'Neue Zahl',
        ready: 'Startbereit...',
        previous_numbers: 'Zuletzt gezogene Zahlen'
    },
    fr: {
        doc_title_operator: "Console d'animation bingo",
        doc_title_display: 'Écran de projection bingo',
        language: 'Langue :',
        console: 'Console :',
        tv_screen: 'Écran TV :',
        dark: 'Sombre',
        light: 'Clair',
        setup_heading: "Configuration de l'animateur bingo",
        setup_subtitle: 'Choisissez comment gérer et démarrer les écrans de bingo.',
        mode_local: 'Mode local',
        mode_local_desc: 'Démarrez directement et ouvrez la projection dans une nouvelle fenêtre sur cet ordinateur.',
        mode_wireless: 'Mode sans fil',
        mode_wireless_desc: 'Connectez plusieurs appareils externes (TV, Raspberry Pi…) sans fil via un code.',
        mode_display: 'Utiliser comme écran',
        mode_display_desc: 'Démarrez cet appareil comme récepteur TV passif pour afficher les numéros de bingo.',
        resume_divider: 'OU REPRENDRE UNE SESSION DE JEU',
        code_placeholder: 'CODE',
        resume_button: 'Reprendre une partie existante',
        game_code_label: 'Code de partie :',
        stop_game: 'Arrêter la partie',
        number_selection: 'Sélection des numéros',
        undo: 'Annuler le dernier',
        reset_board: 'Réinitialiser la grille',
        linked_screens: 'Écrans connectés',
        enter_display_code: "Saisissez un code d'écran pour ajouter un écran supplémentaire :",
        tv_code_placeholder: 'CODE TV',
        link_screen: "Connecter l'écran",
        no_screens: 'Aucun écran actif connecté.',
        tv_code: 'Code TV :',
        err_invalid_code: 'Saisissez un code valide.',
        err_resume: 'Erreur lors de la reprise de la partie.',
        err_network: 'Erreur réseau.',
        err_start_game: "Impossible de démarrer une instance de partie.",
        err_start_multi: 'Erreur lors de la création du jeu multi-écrans.',
        err_display_code: 'Saisissez un code à 4 lettres.',
        err_failed: 'Échec',
        err_conn: 'Erreur de connexion.',
        session_expired: 'Session expirée.',
        confirm_reset: 'Voulez-vous vraiment réinitialiser tous les numéros tirés ?',
        link_screen_title: "Connecter l'écran",
        link_instructions: 'Ouvrez la console bingo sur votre ordinateur et saisissez le code ci-dessus pour démarrer.',
        new_number: 'Nouveau numéro',
        ready: 'Prêt à commencer...',
        previous_numbers: 'Numéros précédents'
    }
};

function detectLang() {
    const saved = localStorage.getItem('bingo_lang');
    if (saved && SUPPORTED_LANGS.includes(saved)) return saved;
    const nav = (navigator.language || DEFAULT_LANG).slice(0, 2).toLowerCase();
    return SUPPORTED_LANGS.includes(nav) ? nav : DEFAULT_LANG;
}

let currentLang = detectLang();

function t(key) {
    const table = I18N[currentLang] || I18N[DEFAULT_LANG];
    return table[key] || I18N[DEFAULT_LANG][key] || key;
}

function applyLanguage() {
    document.documentElement.lang = currentLang;
    const page = document.body.dataset.page;
    if (page && I18N[currentLang]['doc_title_' + page]) {
        document.title = t('doc_title_' + page);
    }
    document.querySelectorAll('[data-i18n]').forEach(el => {
        el.textContent = t(el.dataset.i18n);
    });
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
        el.placeholder = t(el.dataset.i18nPlaceholder);
    });
    const sel = document.getElementById('langSelect');
    if (sel) sel.value = currentLang;
    if (typeof window.onLanguageChange === 'function') window.onLanguageChange();
}

function setLang(lang) {
    if (!SUPPORTED_LANGS.includes(lang)) return;
    currentLang = lang;
    localStorage.setItem('bingo_lang', lang);
    applyLanguage();
}
