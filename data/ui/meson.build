message('Compiling blueprints')


blueprints = custom_target('blueprints',
  input: files(
    'dialogs/account_setup.blp',
    'pages/user.blp',
    'shortcuts.blp',
    'views/sidebar/account_chooser.blp',
    'views/sidebar/account_row.blp',
    'views/sidebar/item.blp',
    'views/sidebar/view.blp',
    'widgets/spinner_button.blp',
    'window.blp',
  ),
  output: '.',
  command: [find_program('blueprint-compiler'), 'batch-compile', '@OUTPUT@', '@CURRENT_SOURCE_DIR@', '@INPUT@'],
)
