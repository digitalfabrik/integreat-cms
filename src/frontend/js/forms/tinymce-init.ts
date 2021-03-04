/**
 * This file initializes the tinymce editor.
 */

let tinymce_config = u("#tinymce-config-options");
tinymce.init({
    selector: '.tinymce_textarea',
    menubar: "edit view insert format icon",
    menu: {
        icon: { title: "Icons", items: "pinicon wwwicon callicon clockicon aticon ideaicon"},
        format: { title: 'Format', items: 'bold italic underline strikethrough superscript | formats | forecolor backcolor' }
    },
    contextmenu: "paste link",
    autosave_interval: '120s',
    forced_root_block : false,
    plugins: "code paste fullscreen autosave link preview media image lists directionality wordcount",
    external_plugins: {
        'autolink_tel': '../js/custom_plugins/autolink_tel/plugin.js'
    },
    link_default_protocol: 'https',
    toolbar: 'bold italic underline forecolor | bullist numlist | styleselect | undo redo | ltr rtl notranslate | aligncenter indent outdent | link image',
    style_formats: [
        { title: 'Headings', items: [
                { title: 'Heading 2', format: 'h2' },
                { title: 'Heading 3', format: 'h3' },
                { title: 'Heading 4', format: 'h4' },
                { title: 'Heading 5', format: 'h5' },
                { title: 'Heading 6', format: 'h6' }
            ]},
        { title: 'Inline', items: [
                { title: 'Bold', format: 'bold' },
                { title: 'Italic', format: 'italic' },
                { title: 'Underline', format: 'underline' },
                { title: 'Strikethrough', format: 'strikethrough' },
                { title: 'Superscript', format: 'superscript' },
                { title: 'Subscript', format: 'subscript' },
                { title: 'Code', format: 'code' }
            ]},
        { title: 'Blocks', items: [
                { title: 'Paragraph', format: 'p' },
                { title: 'Blockquote', format: 'blockquote' },
                { title: 'Div', format: 'div' },
                { title: 'Pre', format: 'pre' }
            ]},
        { title: 'Align', items: [
                { title: 'Left', format: 'alignleft' },
                { title: 'Center', format: 'aligncenter' },
                { title: 'Right', format: 'alignright' },
                { title: 'Justify', format: 'alignjustify' }
            ]}
    ],
    min_height: 400,
    content_css : tinymce_config.data("customcss-src"),
    language: tinymce_config.data("language"),
    setup: (editor) => {
        editor.ui.registry.addButton('notranslate',
            {
                tooltip: tinymce_config.data("notranslate-tooltip"),
                icon: 'no_translate',
                onAction: () => {
                    editor.focus();
                    val = tinymce.activeEditor.dom.getAttrib(tinyMCE.activeEditor.selection.getNode(), "translate", "yes");
                    if(val == "no") {
                        tinymce.activeEditor.dom.setAttrib(tinyMCE.activeEditor.selection.getNode(), "translate", null);
                    } else if (editor.selection.getContent().length > 0) {
                        editor.selection.setContent('<span class="notranslate" translate="no">' + editor.selection.getContent() + '</span>');
                    }
                }
            });
        editor.ui.registry.addIcon('pin_icon', '<svg version="1.1" id="Layer_1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" x="0px" y="0px"	 viewBox="0 0 512 512" style="enable-background:new 0 0 512 512;" xml:space="preserve">		<path d="M256,0C161.896,0,85.333,76.563,85.333,170.667c0,28.25,7.063,56.26,20.49,81.104L246.667,506.5			c1.875,3.396,5.448,5.5,9.333,5.5s7.458-2.104,9.333-5.5l140.896-254.813c13.375-24.76,20.438-52.771,20.438-81.021			C426.667,76.563,350.104,0,256,0z M256,256c-47.052,0-85.333-38.281-85.333-85.333c0-47.052,38.281-85.333,85.333-85.333			s85.333,38.281,85.333,85.333C341.333,217.719,303.052,256,256,256z"/></svg>');
        editor.ui.registry.addIcon('www_icon','<svg version="1.1" id="Capa_1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" x="0px" y="0px"	 viewBox="0 0 26 26" style="enable-background:new 0 0 26 26;" xml:space="preserve">	<path style="fill:#030104;" d="M8.083,11.222L6.419,15c-0.041,0.094-0.144,0.154-0.257,0.154H5.31		c-0.113,0-0.216-0.061-0.256-0.154l-0.79-1.803c-0.077-0.178-0.147-0.348-0.213-0.517c-0.073,0.186-0.148,0.359-0.223,0.525		l-0.833,1.8c-0.042,0.091-0.144,0.149-0.255,0.149H1.888c-0.117,0-0.219-0.063-0.259-0.158l-1.557-3.779		c-0.03-0.074-0.018-0.156,0.034-0.221s0.135-0.103,0.225-0.103H1.29c0.121,0,0.227,0.069,0.263,0.169l0.684,1.92		c0.057,0.162,0.11,0.315,0.159,0.461c0.06-0.146,0.125-0.3,0.194-0.463l0.842-1.932c0.041-0.093,0.143-0.155,0.256-0.155H4.48		c0.115,0,0.217,0.063,0.258,0.157l0.798,1.89c0.072,0.17,0.136,0.329,0.195,0.479c0.049-0.142,0.106-0.296,0.171-0.465l0.737-1.898		c0.038-0.098,0.143-0.164,0.26-0.164h0.926c0.091,0,0.175,0.039,0.227,0.104C8.105,11.064,8.115,11.147,8.083,11.222z		 M17.005,11.222L15.341,15c-0.041,0.094-0.144,0.154-0.256,0.154h-0.854c-0.113,0-0.215-0.061-0.256-0.154l-0.789-1.803		c-0.078-0.178-0.148-0.348-0.214-0.517c-0.073,0.186-0.148,0.359-0.223,0.525l-0.833,1.8c-0.042,0.091-0.143,0.149-0.255,0.149		h-0.853c-0.116,0-0.219-0.063-0.259-0.158l-1.557-3.779c-0.03-0.074-0.018-0.156,0.034-0.221c0.052-0.064,0.136-0.103,0.225-0.103		h0.959c0.121,0,0.227,0.069,0.263,0.169l0.683,1.92c0.057,0.162,0.11,0.315,0.161,0.461c0.059-0.146,0.123-0.3,0.192-0.463		l0.843-1.932c0.04-0.093,0.142-0.155,0.256-0.155H13.4c0.115,0,0.218,0.063,0.258,0.157l0.799,1.89		c0.071,0.17,0.135,0.329,0.193,0.479c0.051-0.142,0.106-0.296,0.172-0.465l0.737-1.898c0.038-0.098,0.144-0.164,0.261-0.164h0.926		c0.092,0,0.177,0.039,0.227,0.104C17.026,11.064,17.038,11.147,17.005,11.222z M25.926,11.222L24.263,15		c-0.042,0.094-0.144,0.154-0.257,0.154h-0.853c-0.113,0-0.216-0.061-0.256-0.154l-0.789-1.803		c-0.078-0.178-0.148-0.348-0.214-0.517c-0.073,0.186-0.149,0.359-0.224,0.525l-0.833,1.8c-0.042,0.091-0.144,0.149-0.255,0.149		H19.73c-0.117,0-0.22-0.063-0.26-0.158l-1.557-3.779c-0.029-0.074-0.019-0.156,0.033-0.221s0.136-0.103,0.226-0.103h0.96		c0.121,0,0.227,0.069,0.262,0.169l0.684,1.92c0.057,0.162,0.11,0.315,0.16,0.461c0.059-0.146,0.123-0.3,0.192-0.463l0.843-1.932		c0.041-0.093,0.143-0.155,0.257-0.155h0.791c0.115,0,0.218,0.063,0.258,0.157l0.798,1.89c0.072,0.17,0.137,0.329,0.196,0.479		c0.049-0.142,0.106-0.296,0.171-0.465l0.738-1.898c0.037-0.098,0.142-0.164,0.26-0.164h0.926c0.092,0,0.176,0.039,0.227,0.104		C25.946,11.064,25.958,11.147,25.926,11.222z"/>		<path style="fill:#030104;" d="M2.71,9c0.283-0.718,0.637-1.401,1.057-2.037C3.829,6.975,3.887,7,3.952,7h1.88			c-0.199,0.634-0.355,1.309-0.49,2h2.055c0.155-0.699,0.335-1.376,0.562-2h9.986c0.227,0.624,0.407,1.301,0.562,2h2.055			c-0.135-0.691-0.291-1.366-0.49-2h1.88c0.065,0,0.123-0.025,0.186-0.037C22.556,7.599,22.911,8.282,23.194,9h2.121			c-1.691-5.216-6.591-9-12.363-9S2.28,3.784,0.588,9H2.71z M20.478,5H19.29c-0.258-0.543-0.542-1.05-0.851-1.519			C19.179,3.909,19.861,4.419,20.478,5z M12.952,2c1.551,0,2.983,1.154,4.062,3H8.89C9.969,3.154,11.401,2,12.952,2z M7.463,3.481			C7.155,3.95,6.871,4.457,6.613,5H5.426C6.043,4.419,6.725,3.909,7.463,3.481z"/>		<path style="fill:#030104;" d="M23.194,17c-0.283,0.719-0.638,1.4-1.057,2.037C22.075,19.025,22.017,19,21.952,19h-1.881			c0.199-0.634,0.355-1.309,0.49-2h-2.055c-0.154,0.699-0.335,1.377-0.562,2H7.959c-0.227-0.623-0.407-1.301-0.562-2H5.343			c0.135,0.691,0.291,1.366,0.49,2H3.952c-0.065,0-0.123,0.025-0.185,0.037C3.348,18.4,2.993,17.719,2.71,17H0.588			c1.692,5.216,6.592,9,12.364,9s10.672-3.784,12.363-9H23.194z M5.426,21h1.188c0.258,0.543,0.542,1.051,0.85,1.519			C6.725,22.091,6.043,21.581,5.426,21z M12.952,24c-1.551,0-2.983-1.154-4.062-3h8.123C15.935,22.846,14.503,24,12.952,24z			 M18.44,22.519c0.309-0.468,0.593-0.976,0.851-1.519h1.188C19.861,21.581,19.179,22.091,18.44,22.519z"/></svg>');
        editor.ui.registry.addIcon('call_icon', '<svg version="1.1" id="Capa_1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" x="0px" y="0px"	 width="16" height="16" viewBox="0 0 348.077 348.077" style="enable-background:new 0 0 348.077 348.077;"	 xml:space="preserve">			<path d="M340.273,275.083l-53.755-53.761c-10.707-10.664-28.438-10.34-39.518,0.744l-27.082,27.076				c-1.711-0.943-3.482-1.928-5.344-2.973c-17.102-9.476-40.509-22.464-65.14-47.113c-24.704-24.701-37.704-48.144-47.209-65.257				c-1.003-1.813-1.964-3.561-2.913-5.221l18.176-18.149l8.936-8.947c11.097-11.1,11.403-28.826,0.721-39.521L73.39,8.194				C62.708-2.486,44.969-2.162,33.872,8.938l-15.15,15.237l0.414,0.411c-5.08,6.482-9.325,13.958-12.484,22.02				C3.74,54.28,1.927,61.603,1.098,68.941C-6,127.785,20.89,181.564,93.866,254.541c100.875,100.868,182.167,93.248,185.674,92.876				c7.638-0.913,14.958-2.738,22.397-5.627c7.992-3.122,15.463-7.361,21.941-12.43l0.331,0.294l15.348-15.029				C350.631,303.527,350.95,285.795,340.273,275.083z"/></svg>');
        editor.ui.registry.addIcon('clock_icon', '<svg version="1.1" id="Capa_1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" x="0px" y="0px"	 width="16" height="16" viewBox="0 0 468.067 468.067" style="enable-background:new 0 0 468.067 468.067;"	 xml:space="preserve">	<path d="M431.38,0.225H36.685C16.458,0.225,0,16.674,0,36.898v394.268c0,20.221,16.458,36.677,36.685,36.677H431.38		c20.232,0,36.688-16.456,36.688-36.677V36.898C468.062,16.668,451.606,0.225,431.38,0.225z M406.519,41.969		c8.678,0,15.711,7.04,15.711,15.72c0,8.683-7.033,15.717-15.711,15.717c-8.688,0-15.723-7.04-15.723-15.717		C390.796,49.009,397.83,41.969,406.519,41.969z M350.189,41.969c8.688,0,15.723,7.04,15.723,15.72		c0,8.683-7.034,15.717-15.723,15.717c-8.684,0-15.711-7.04-15.711-15.717C334.479,49.009,341.513,41.969,350.189,41.969z		 M426.143,425.924H41.919V112.429h384.224V425.924z M234.031,385.902c66.212,0,120.095-53.871,120.095-120.096		c0-66.221-53.883-120.095-120.095-120.095c-66.215,0-120.095,53.874-120.095,120.095		C113.936,332.031,167.815,385.902,234.031,385.902z M234.031,169.923c52.866,0,95.884,43.016,95.884,95.884		c0,52.866-43.019,95.885-95.884,95.885c-52.869,0-95.884-43.019-95.884-95.885C138.146,212.938,181.162,169.923,234.031,169.923z		 M221.926,265.807v-60.526c0-6.682,5.423-12.105,12.105-12.105s12.105,5.423,12.105,12.105v48.42h49.935		c6.679,0,12.105,5.427,12.105,12.105c0,6.68-5.427,12.105-12.105,12.105h-62.04C227.349,277.912,221.926,272.486,221.926,265.807z"		/></svg>');
        editor.ui.registry.addIcon('email_icon', '<svg version="1.1" id="Capa_1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" x="0px" y="0px"	 viewBox="0 0 490.2 490.2" style="enable-background:new 0 0 490.2 490.2;" xml:space="preserve"><g>	<path d="M420.95,61.8C376.25,20.6,320.65,0,254.25,0c-69.8,0-129.3,23.4-178.4,70.3s-73.7,105.2-73.7,175		c0,66.9,23.4,124.4,70.1,172.6c46.9,48.2,109.9,72.3,189.2,72.3c47.8,0,94.7-9.8,140.7-29.5c15-6.4,22.3-23.6,16.2-38.7l0,0		c-6.3-15.6-24.1-22.8-39.6-16.2c-40,17.2-79.2,25.8-117.4,25.8c-60.8,0-107.9-18.5-141.3-55.6c-33.3-37-50-80.5-50-130.4		c0-54.2,17.9-99.4,53.6-135.7c35.6-36.2,79.5-54.4,131.5-54.4c47.9,0,88.4,14.9,121.4,44.7s49.5,67.3,49.5,112.5		c0,30.9-7.6,56.7-22.7,77.2c-15.1,20.6-30.8,30.8-47.1,30.8c-8.8,0-13.2-4.7-13.2-14.2c0-7.7,0.6-16.7,1.7-27.1l18.6-152.1h-64		l-4.1,14.9c-16.3-13.3-34.2-20-53.6-20c-30.8,0-57.2,12.3-79.1,36.8c-22,24.5-32.9,56.1-32.9,94.7c0,37.7,9.7,68.2,29.2,91.3		c19.5,23.2,42.9,34.7,70.3,34.7c24.5,0,45.4-10.3,62.8-30.8c13.1,19.7,32.4,29.5,57.9,29.5c37.5,0,69.9-16.3,97.2-49		c27.3-32.6,41-72,41-118.1C488.05,152.9,465.75,103,420.95,61.8z M273.55,291.9c-11.3,15.2-24.8,22.9-40.5,22.9		c-10.7,0-19.3-5.6-25.8-16.8c-6.6-11.2-9.9-25.1-9.9-41.8c0-20.6,4.6-37.2,13.8-49.8s20.6-19,34.2-19c11.8,0,22.3,4.7,31.5,14.2		s13.8,22.1,13.8,37.9C290.55,259.2,284.85,276.6,273.55,291.9z"/></g></svg>');
        editor.ui.registry.addIcon('idea_icon', '<svg version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="16" height="16" viewBox="0 0 16 16"><path fill="#444444" d="M11.7 1.9c-1-1.2-2.6-1.9-4.2-1.9s-3.2 0.7-4.2 1.9c-1 1.1-1.4 2.6-1.2 4 0.2 1.5 0.8 2.6 2.1 3.7 0.5 0.4 0.7 0.8 0.9 1.2 0 0.1 0.1 0.2 0.1 0.3-0.1 0.1-0.2 0.2-0.2 0.4 0 0.3 0.2 0.5 0.5 0.5-0.3 0-0.5 0.2-0.5 0.5s0.2 0.5 0.5 0.5c-0.3 0-0.5 0.2-0.5 0.5s0.2 0.5 0.5 0.5c-0.3 0-0.5 0.2-0.5 0.5s0.2 0.5 0.5 0.5h0.5c0 0.5 0.7 1 1.5 1s1.5-0.5 1.5-1h0.5c0.3 0 0.5-0.2 0.5-0.5s-0.2-0.5-0.5-0.5c0.3 0 0.5-0.2 0.5-0.5s-0.2-0.5-0.5-0.5c0.3 0 0.5-0.2 0.5-0.5s-0.2-0.5-0.5-0.5c0.3 0 0.5-0.2 0.5-0.5 0-0.2-0.1-0.3-0.2-0.4 0-0.1 0.1-0.1 0.1-0.2 0.2-0.4 0.4-0.8 0.9-1.2 1.3-1.1 1.9-2.2 2.1-3.8 0.2-1.4-0.2-2.8-1.2-4zM12 5.8c-0.2 1.3-0.7 2.2-1.8 3.2-0.6 0.5-0.9 1-1.2 1.4-0.2 0.5-0.3 0.6-0.5 0.6h-2c-0.2 0-0.3-0.1-0.5-0.6-0.2-0.4-0.5-1-1.1-1.6-1.3-1.1-1.6-2-1.8-3-0.2-1.1 0.2-2.3 0.9-3.2 0.9-1 2.2-1.6 3.5-1.6s2.6 0.6 3.5 1.6c0.7 0.9 1.1 2.1 1 3.2z"></path><path fill="#444444" d="M11 5h-1c0-0.7-0.8-2-2-2v-1c1.8 0 3 1.8 3 3z"></path></svg>');
        editor.ui.registry.addIcon('no_translate', '<svg version="1.0" xmlns="http://www.w3.org/2000/svg" width="18pt" height="16pt" viewBox="0 0 30.000000 28.000000" preserveAspectRatio="xMidYMid meet"> <g transform="translate(0.000000,28.000000) scale(0.100000,-0.100000)" fill="#000000" stroke="none"> <path d="M187 236 c-5 -12 -21 -16 -67 -16 l-60 0 0 -100 0 -101 68 3 67 3 3 70 c3 69 4 71 33 82 25 10 30 16 27 40 -2 23 -8 29 -34 31 -21 2 -33 -2 -37 -12z m61 -23 c2 -15 -3 -23 -20 -28 -13 -4 -35 -19 -50 -33 -37 -34 -49 -20 -15 16 15 16 27 35 27 43 0 22 11 30 35 27 12 -2 21 -12 23 -25z"/> </g> </svg>')
        editor.ui.registry.addMenuItem('pinicon', {
            text: tinymce_config.data("pinicon-text"),
            icon: 'pin_icon',
            onAction: function () {
                editor.insertContent('<img src="' + tinymce_config.data("pinicon-src") + '" style="width:15px; height:15px">');
            }
        });
        editor.ui.registry.addMenuItem('wwwicon', {
            text: tinymce_config.data("wwwicon-text"),
            icon: 'www_icon',
            onAction: function () {
                editor.insertContent('<img src="' + tinymce_config.data("wwwicon-src") + '" style="width:15px; height:15px">');
            }
        });
        editor.ui.registry.addMenuItem('callicon', {
            text: tinymce_config.data("callicon-text"),
            icon: 'call_icon',
            onAction: function () {
                editor.insertContent('<img src="' + tinymce_config.data("callicon-src") + '" style="width:15px; height:15px">');
            }
        });
        editor.ui.registry.addMenuItem('clockicon', {
            text: tinymce_config.data("clockicon-text"),
            icon: 'clock_icon',
            onAction: function () {
                editor.insertContent('<img src="' + tinymce_config.data("clockicon-src") + '" style="width:15px; height:15px">');
            }
        });
        editor.ui.registry.addMenuItem('aticon', {
            text: tinymce_config.data("aticon-text"),
            icon: 'email_icon',
            onAction: function () {
                editor.insertContent('<img src="' + tinymce_config.data("aticon-src") + '" style="width:15px; height:15px">');
            }
        });
        editor.ui.registry.addMenuItem('ideaicon', {
            text: tinymce_config.data("ideaicon-text"),
            icon: 'idea_icon',
            onAction: function () {
                editor.insertContent('<img src="' + tinymce_config.data("ideaicon-src") + '" style="width:15px; height:15px">');
            }
        });
    },
    readonly : tinymce_config.data("readonly"),
    init_instance_callback: function(editor) {
        editor.on('StoreDraft', autosave_editor);
    }
});
