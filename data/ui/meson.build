message('Compiling blueprints')


blueprints = custom_target('blueprints',
  input: files(
    'dialogs/login.blp',
    'shortcuts.blp',
    'widgets/spinner_button.blp',
    'views/sidebar/view.blp',
    'views/sidebar/account_chooser.blp',
    'views/sidebar/account_row.blp',
    'views/sidebar/item.blp',
    'window.blp',
  ),
  output: '.',
  command: [find_program('blueprint-compiler'), 'batch-compile', '@OUTPUT@', '@CURRENT_SOURCE_DIR@', '@INPUT@'],
)
