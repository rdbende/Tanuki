message('Compiling blueprints')


blueprints = custom_target('blueprints',
  input: files(
    'window.blp',
    'shortcuts.blp',
  ),
  output: '.',
  command: [find_program('blueprint-compiler'), 'batch-compile', '@OUTPUT@', '@CURRENT_SOURCE_DIR@', '@INPUT@'],
)
