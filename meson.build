project('io.github.rdbende.Tanuki',
          version: '0.1.0',
    meson_version: '>= 0.62.0',
  default_options: [ 'warning_level=2', 'werror=false', ],
)

i18n = import('i18n')
gnome = import('gnome')
python = import('python')

py_installation = python.find_installation('python3')

python_dir = get_option('prefix') / py_installation.get_install_dir()
pkgdatadir = get_option('prefix') / get_option('datadir') / meson.project_name()
localedir = get_option('prefix') / get_option('localedir')
bindir = get_option('prefix') / get_option('bindir')
moduledir = python_dir / 'tanuki'


conf = configuration_data()
conf.set('PYTHON', py_installation.full_path())
conf.set('VERSION', meson.project_version())
conf.set('APP-ID', meson.project_name())
conf.set('APP-ICON', meson.project_name())
conf.set('LOCALEDIR', localedir)
conf.set('PKGDATADIR', pkgdatadir)


subdir('data')
subdir('po')


install_subdir(
  'src',
  install_dir: moduledir,
  strip_directory: true
)

configure_file(
  input: 'src/io.github.rdbende.Tanuki.in',
  output: 'io.github.rdbende.Tanuki',
  configuration: conf,
  install: true,
  install_dir: bindir,
  install_mode: 'r-xr-xr-x'
)

configure_file(
  input: 'src/__init__.py',
  output: '__init__.py',
  configuration: conf,
  install: true,
  install_dir: moduledir,
)


gnome.post_install(
     glib_compile_schemas: true,
    gtk_update_icon_cache: true,
  update_desktop_database: true,
)
