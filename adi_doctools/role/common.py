import subprocess
from docutils import nodes
from sphinx.util import logging

logger = logging.getLogger(__name__)

# Default values
dft_url_dokuwiki = 'https://wiki.analog.com'
dft_url_ez = 'https://ez.analog.com'
dft_url_mw = 'https://www.mathworks.com'
dft_url_git_gui = 'https://github.com/analogdevicesinc/{repo}/tree'
dft_url_git_raw = 'https://raw.githubusercontent.com/analogdevicesinc/{repo}'
dft_url_adi = 'https://www.analog.com'
dft_url_xilinx = 'https://www.xilinx.com'
dft_url_intel = 'https://www.intel.com'

git_repos = [
    # url_path           name
    ['hdl',              "HDL"],
    ['testbenches',      "Testbenches"],
    ['linux',            "Linux"],
    ['no-OS',            "no-OS"],
    ['libiio',           "libiio"],
    ['scopy',            "Scopy"],
    ['iio-oscilloscope', "IIO Oscilloscope"],
    ['doctools',         "Doctools"],
    ['documentation',    "System Level Documentation"],
    ['pyadi-iio',        "PyADI-IIO"],
    ['meta-adi',         "META-ADI"],
    ['wiki-scripts',     "Wiki Scripts"]
]
vendors = ['xilinx', 'intel', 'mw']


def get_url_config(name, inliner):
    app = inliner.document.settings.env.app
    return getattr(app.config, "url_"+name)


def get_outer_inner(text):
    """
    Extract 'outer <inner>' fields.
    """
    pos = text.find('<')
    if pos != -1 and text[len(text)-1] == '>':
        return (text[0:pos].strip(), text[pos+1:-1])
    else:
        return (None, text)


def color(class_name):
    def role(name, rawtext, text, lineno, inliner, options={}, content=[]):
        node = nodes.inline(text=text, classes=[class_name])
        return [node], []

    return role


def datasheet():
    def role(name, rawtext, text, lineno, inliner, options={}, content=[]):
        # DEPRECATED
        logger.info("The datasheet role has been deprecated, use the adi role "
                    "instead.")
        return [], []

    return role


def dokuwiki():
    def role(name, rawtext, text, lineno, inliner, options={}, content=[]):
        text, path = get_outer_inner(text)
        if text is None:
            text = path[path.rfind('/')+1:]
        url = get_url_config('dokuwiki', inliner) + '/' + path
        node = nodes.reference(rawtext, text, refuri=url, **options)
        return [node], []

    return role


def ez():
    def role(name, rawtext, text, lineno, inliner, options={}, content=[]):
        text, path = get_outer_inner(text)
        if path == '/':
            path = ''
        url = get_url_config('ez', inliner) + '/' + path
        if text is None:
            text = "EngineerZone"
        node = nodes.reference(rawtext, text, refuri=url,
                               classes=['icon', 'ez'], **options)
        return [node], []

    return role


def get_default_brach(repo, inliner):
    """
    Get default branch for each repo.
    If it is not known, returns 'main'
    """
    app = inliner.document.settings.env.app
    if repo in app.lut['repos']:
        return app.lut['repos'][repo]['branch']
    else:
        return 'main'


def git(repo, alt_name):
    def role(name, rawtext, text, lineno, inliner, options={}, content=[]):
        text, path = get_outer_inner(text)

        pos = path.find('+')
        if path[0:pos] == "raw":
            type_ = path[0:pos]
        else:
            type_ = "gui"
        path = path[pos+1:]

        pos = path.find(':')
        if pos in [0, -1]:
            branch = get_default_brach(repo, inliner)
        else:
            branch = path[0:pos]
        path = path[pos+1:]
        if text is None:
            if path == '/':
                text = "ADI " + alt_name + " repository"
            else:
                text = path
        if path == '/':
            path = ''

        url = get_url_config('git_'+type_, inliner).format(repo=repo)
        url = url + '/' + branch + '/' + path
        node = nodes.reference(rawtext, text, refuri=url,
                               classes=['icon', 'git'], **options)
        return [node], []

    return role


def adi():
    def role(name, rawtext, text, lineno, inliner, options={}, content=[]):
        name, adi_id = get_outer_inner(text)
        if name is None:
            name = adi_id
        url = get_url_config('adi', inliner) + '/' + adi_id
        node = nodes.reference(rawtext, name, refuri=url,
                               classes=['icon', 'adi'], **options)
        return [node], []

    return role


def vendor(vendor_name):
    def role(name, rawtext, text, lineno, inliner, options={}, content=[]):
        text, path = get_outer_inner(text)
        if text is None:
            text = path[path.rfind('/')+1:]
        url = get_url_config(vendor_name, inliner) + '/' + path
        node = nodes.reference(rawtext, text, refuri=url, **options)
        return [node], []

    return role


def common_setup(app):
    app.add_role("red",             color('red'))
    app.add_role("green",           color('green'))
    app.add_role("datasheet",       datasheet())
    app.add_role("dokuwiki",        dokuwiki())
    app.add_role("ez",              ez())
    app.add_role("adi",             adi())
    for name in vendors:
        app.add_role(name,          vendor(name))
    for path, name in git_repos:
        app.add_role("git-"+path,   git(path, name))

    app.add_config_value('url_dokuwiki',  dft_url_dokuwiki,  'env')
    app.add_config_value('url_ez',        dft_url_ez,        'env')
    app.add_config_value('url_mw',        dft_url_mw,        'env')
    app.add_config_value('url_git_gui',   dft_url_git_gui,   'env')
    app.add_config_value('url_git_raw',   dft_url_git_raw,   'env')
    app.add_config_value('url_adi',       dft_url_adi,       'env')
    app.add_config_value('url_xilinx',    dft_url_xilinx,    'env')
    app.add_config_value('url_intel',     dft_url_intel,     'env')
