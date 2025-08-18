import { languages } from 'monaco-editor';

export const nixLanguage: languages.IMonarchLanguage = {
	defaultToken: '',

	ignoreCase: false,

	keywords: ['let', 'in', 'rec', 'with', 'inherit', 'import', 'if', 'then', 'else', 'assert', 'or'],

	constants: ['true', 'false', 'null'],

	brackets: [
		{ open: '{', close: '}', token: 'delimiter.curly' },
		{ open: '[', close: ']', token: 'delimiter.square' },
		{ open: '(', close: ')', token: 'delimiter.parenthesis' }
	],

	tokenizer: {
		root: [
			// comments
			[/#.*$/, 'comment'],
			[/\/\*/, { token: 'comment', next: '@comment' }],

			// strings
			[/''/, { token: 'string.quote', next: '@indentedString' }],
			[/"/, { token: 'string.quote', next: '@string' }],

			// numbers
			[/\d+\.\d+/, 'number.float'],
			[/\d+/, 'number'],

			// operators and delimiters
			[/[=><!~?:&|+\-*/^%]+/, 'operator'],
			[/[@;]/, 'delimiter'],

			// brackets
			[/[{}\[\]()]/, '@brackets'],

			// identifiers and keywords
			[
				/[a-zA-Z_][a-zA-Z0-9_]*/,
				{
					cases: {
						'@keywords': 'keyword',
						'@constants': 'constant',
						'@default': 'identifier'
					}
				}
			],

			// whitespace
			{ include: '@whitespace' }
		],

		whitespace: [[/[ \t\r\n]+/, 'white']],

		comment: [
			[/[^/*]+/, 'comment'],
			[/\/\*/, 'comment', '@push'], // nested comments
			[/\*\//, 'comment', '@pop'],
			[/[\/*]/, 'comment']
		],

		string: [
			[/[^"\\$]+/, 'string'], // normal string content
			[/\\./, 'string.escape'], // escaped characters
			[/\$\{/, { token: 'delimiter.bracket', next: '@interpolation' }], // interpolation
			[/"/, { token: 'string.quote', next: '@pop' }]
		],

		indentedString: [
			[/[^'$]+/, 'string'],
			[/\$\{/, { token: 'delimiter.bracket', next: '@interpolationIndented' }],
			[/''/, { token: 'string.quote', next: '@pop' }]
		],

		interpolation: [
			[/\}/, { token: 'delimiter.bracket', next: '@pop' }], // back to string
			{ include: 'root' } // allow full nix expression
		],

		interpolationIndented: [
			[/\}/, { token: 'delimiter.bracket', next: '@pop' }],
			{ include: 'root' }
		]
	}
};

export const nixLanguageConfiguration: languages.LanguageConfiguration = {
	// comments: '#' for single line, /* ... */ for block
	comments: {
		lineComment: '#',
		blockComment: ['/*', '*/']
	},

	brackets: [
		['{', '}'],
		['[', ']'],
		['(', ')']
	],

	autoClosingPairs: [
		{ open: '{', close: '}' },
		{ open: '[', close: ']' },
		{ open: '(', close: ')' },
		{ open: '"', close: '"', notIn: ['string'] },
		{ open: "''", close: "''", notIn: ['string'] },
		{ open: '/*', close: '*/', notIn: ['string', 'comment'] }
	],

	surroundingPairs: [
		{ open: '{', close: '}' },
		{ open: '[', close: ']' },
		{ open: '(', close: ')' },
		{ open: '"', close: '"' },
		{ open: "''", close: "''" }
	],

	colorizedBracketPairs: [
		['{', '}'],
		['[', ']'],
		['(', ')']
	],

	// Word pattern for identifiers (Nix identifiers, attributes, etc.)
	wordPattern: /(-?\d*\.\d\w*)|([^\s`~!@#%^&*()+={}\[\]|\\;:'",.<>/?]+)/g,

	folding: {
		markers: {
			// Allow block comment folding
			start: /^\s*\/\*\s*#?region\b/,
			end: /^\s*\/\*\s*#?endregion\b/
		}
	},

	indentationRules: {
		// Increase indent after opening brace or after let/rec/with
		increaseIndentPattern: /(\{[^}"']*|\blet\b|\brec\b|\bwith\b).*$/,
		// Decrease indent after closing brace
		decreaseIndentPattern: /^\s*\}/
	},

	onEnterRules: [
		{
			// Auto-indent between curly braces
			beforeText: /^\s*{\s*$/,
			action: { indentAction: languages.IndentAction.Indent }
		},
		{
			// Outdent when closing brace
			beforeText: /^\s*}\s*$/,
			action: { indentAction: languages.IndentAction.Outdent }
		}
	]
};
