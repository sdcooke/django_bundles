# django_bundles: Another Django media bundler

django_bundles is a media bundler for Django. It can be used to bundle groups of media files (e.g. CSS, JavaScript) into a single file with a hash in the filename (to play nicely with browser caching) whilst keeping the files separate during development.

There are ideas taken from a lot of the other media bundlers - none of them worked quite how I wanted and I fancied writing my own.

I think Django 1.4 is required, but possibly only because of the assignment tag decorator used.

IMPORTANT NOTE: 0.3.0 is not backwards compatible with 0.2.5

## Features

* Pre and post processing of files (e.g. LessCSS, UglifyJS) - really easy to add others
* Could be used with script loaders either using the template tags for inline scripts or a DjangoTemplateProcessor to preprocess a JavaScript file
* Management command to bundle media
* Management command to lint files (e.g. using JSLint/JSHint)
* Flexible API that doesn't force you to work in a certain way

## Usage

The main settings are `USE_BUNDLES` which is True/False to enable/disable bundling in the template (defaults to `not settings.DEBUG`), `BUNDLES_VERSION_FILE` which is where versions are stored (in a python file) and `BUNDLES` which looks like:

```python
BUNDLES = (
    ('master_css', {
        'type': 'css',
        'files': (
            'css/*.css',
            'css/more/test3.css',
            'less/test.less',
        ),
    }),
    ('master_js', {
        'type': 'js',
        'files': (
            'js/*.js',
        )
    }),
    ('script_loader_example', {
        'type': 'js',
        'files': (
            'script_loader_example.js',
        ),
        'processors': (
            'django_bundles.processors.django_template.DjangoTemplateProcessor',
        )
    }),
)
```

All of the `BUNDLES` options can be found in django_bundles/core.py on the `Bundle` and `BundleFile` classes.

The `{% render_bundle bundle_name %}` template tag can then be used to render the HTML (e.g. script or link tag) in place. django_bundles/templates needs to be in your template directories list (or copy them in).

Other settings are (check out django_bundles/conf/default_settings.py):

* `DEFAULT_PREPROCESSORS` - dict of file type to list of processors (default is LessCSS for .less files)
* `DEFAULT_POSTPROCESSORS` - dict of bundle type to list of processors (default is UglifyJS for .js bundles)

## Linting

If you define a `BUNDLES_LINTING` setting you can use the `lint_bundles` management command to lint your files. e.g.

```python
BUNDLES_LINTING = {
    'js': {
        'command': '/path/to/jslint/bin/jslint.js {infile}',
        'default': True,
    },
}
```

It currently expects output like JSLint.

## Things it doesn't do

* JavaScript tags are rendered in place in the template - there's no deferring them to the bottom of the page automatically
* Files aren't passed through preprocessors before being rendered in development mode - for LessCSS you have to include the LessCSS script tag (wrapped in `{% if not settings.USE_BUNDLES %}` so you don't use it in production)

## staticfiles

I think it should be pretty simple to use this with staticfiles with clever use of `files_url_root`, `files_root`, `bundle_url_root` and `bundle_file_root` as long as `collectstatic` management command is run before `create_bundles` in the deployment process.
