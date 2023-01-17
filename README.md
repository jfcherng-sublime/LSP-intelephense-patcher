# ST-LSP-intelephense-patcher

It only costs \$10 USD to get a life-time license for `intelephense` premium.

## Intelephense Premium Features

![Premium features](https://raw.githubusercontent.com/jfcherng-sublime/ST-LSP-intelephense-patcher/master/docs/premium-features.png)

See https://intelephense.com/

- Rename: Easily rename symbols with automatic file/folder renaming too.
- Code folding: Accurate folding of definitions, blocks, use declarations, heredoc, comments, and custom regions.
- Find all implementations: Quickly find implementations of interfaces, abstract classes and associated methods.
- Go to type definition Quickly navigate to variables and parameter type definitions.
- Go to declaration: Quickly navigate to interface or abstract method declarations.
- Smart select: Intelligently expand/shrink text selection based on parse tree.
- Code actions: Import symbols, add (template configurable) PHPDoc, and implement all abstract methods.

## Installation

This plugin will never be published on Package Control.

To install this plugin via Package Control, you have to add a custom repository.

1. Execute `Package Control: Add Repository` in the command palette.
1. Add this custom repository: `https://raw.githubusercontent.com/jfcherng-sublime/ST-my-package-control/master/repository.json`
1. Restart Sublime Text.
1. You should be able to install this package with Package Control with the name `LSP-intelephense-patcher`.

## Usage

After installation, to use this plugin, you need to have following things installed as well.

- [LSP](https://packagecontrol.io/packages/LSP)
- [LSP-intelephense](https://packagecontrol.io/packages/LSP-intelephense)
- The `intelephense` server, which should be installed when you first time open a PHP file in a project.

Then, you can patch the `intelephense` server from the command palette:

- `LSP-intelephense-patcher: Show Menu`

  - `Patch Intelephense` (usually you want to do this)
  - `Patch Intelephense (Allow Unsupported)` (we don't claim the server version supported but you want to give it a try)
  - `Un-patch Intelephense` (restore the patched server back to un-patched)
  - `Re-patch Intelephense` (i.e., `Un-patch` and then `Patch`)
  - `Open Server Binary Directory`

You will have to patch the server again if the server gets updated.
