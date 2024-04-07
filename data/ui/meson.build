message('Compiling blueprints')


blueprints = custom_target('blueprints',
  input: files(
    'login_dialog.blp',
    'shortcuts.blp',
    'widgets/spinner_button.blp',
    'window.blp',
  ),
  output: '.',
  command: [find_program('blueprint-compiler'), 'batch-compile', '@OUTPUT@', '@CURRENT_SOURCE_DIR@', '@INPUT@'],
)
