import click
import subprocess
import re
from os import path, walk, pardir, chdir, getcwd
from glob import glob

from ..typings.hdl import vendors, Library, Carrier
from ..parser.hdl import parse_hdl_regmap
from ..parser.hdl import resolve_hdl_regmap
from ..parser.hdl import expand_hdl_regmap
from ..parser.hdl import parse_hdl_vendor
from ..parser.hdl import parse_hdl_library
from ..parser.hdl import resolve_hdl_library
from ..parser.hdl import parse_hdl_project
from ..parser.hdl import resolve_hdl_project
from ..parser.hdl import parse_hdl_interfaces
from ..writer.hdl import write_hdl_regmap
from ..writer.hdl import write_hdl_library_makefile
from ..writer.hdl import write_hdl_project_makefile


@click.command()
@click.option(
    '--input',
    '-i',
    'input_',
    is_flag=False,
    type=click.Path(exists=True),
    default='.',
    help="Path to any folder in the HDL repo."
)
def hdl_gen(input_):

    global has_tb

    p_ = subprocess.run("git rev-parse --show-toplevel", shell=True,
                        capture_output=True, cwd=input_)
    if p_.returncode != 0:
        click.echo(p_.stderr)
        return

    hdldir = p_.stdout.decode("utf-8").strip().replace('/testbenches', '')
    call_dir = getcwd()
    chdir(hdldir)

    if not path.isfile('LICENSE_ADIJESD204'):
        click.echo("'LICENSE_ADIJESD204' not found,"
                   " are you sure this is the HDL repo?")
        return

    if not (has_tb := path.isdir('testbenches')):
        click.echo("'testbenches' not found, tb files will be skipped.")

    # Generate HDL carrier dictionary
    carrier = Carrier()
    for v in vendors:
        file_ = path.join('projects', 'scripts', f"adi_project_{v}.tcl")
        carrier[v], msg = parse_hdl_vendor(file_)
        for m in msg:
            click.echo(f"{file_}: {m}")

    # TODO do something with the parsed carriers, like get/validate library and
    # project dicts

    # Generate HDL Library dictionary
    types = ['*_ip.tcl', '*_hw.tcl']
    files = {}
    library = {}
    project = {}
    interfaces_ip_files = []
    for v in vendors:
        files[v] = []
    for typ, v in zip(types, vendors):
        glob_ = path.join('library', '**', typ)
        files[v].extend(glob(glob_, recursive=True))

    for v in files:
        for f in files[v]:
            if 'interfaces_ip.tcl' in f:
                files[v].remove(f)
                interfaces_ip_files.append(f)

    # Generate the HDL interfaces dictionary
    interfaces_ip = {}
    for f in interfaces_ip_files:
        interfaces_ip[path.dirname(f)] = parse_hdl_interfaces(f)

    intf_key_file = {}
    for f in interfaces_ip:
        for k in interfaces_ip[f]:
            intf_key_file[k['name']] = f

    # Generate the HDL library dictionary
    # A folder may contain variants of the lib per vendor
    for typ, v in zip(types, files):
        for f in files[v]:
            lib_, path_, ip_name = parse_hdl_library(f)
            if lib_:
                if path_ not in library:
                    library[path_] = Library(
                        name=ip_name,
                        vendor={},
                        generic={}
                    )
                library[path_]['vendor'][v] = lib_

    for key in library:
        resolve_hdl_library(library, key, intf_key_file)

    for key in library:
        write_hdl_library_makefile(library, key)

    # Generate HDL Project dictionary
    # A folder contains only one project/vendor
    types = ['system_bd.tcl', 'system_qsys.tcl']
    files = {}
    for v in vendors:
        files[v] = []
    for typ, v in zip(types, vendors):
        glob_ = path.join('projects', '**', typ)
        files[v].extend(glob(glob_, recursive=True))

    for typ, v in zip(types, files):
        for f in files[v]:
            prj_, path_ = parse_hdl_project(f)
            if prj_:
                prj_['vendor'] = v
                project[path_] = prj_

    for key in project:
        resolve_hdl_project(project[key], library)

    for key in project:
        write_hdl_project_makefile(project, key)

    # Generate HDL Register Map dictionary
    rm = {}
    regdir = path.join('docs', 'regmap')
    for (dirpath, dirnames, filenames) in walk(regdir):
        for file in filenames:
            file_ = path.join(dirpath, file)
            m = re.search("adi_regmap_(\\w+)\\.txt", file)
            if not bool(m):
                continue

            reg_name = m.group(1)
            ctime = path.getctime(file_)
            rm[reg_name] = parse_hdl_regmap(ctime, file_)
    resolve_hdl_regmap(rm)
    expand_hdl_regmap(rm)

    if has_tb:
        f_ = path.join('testbenches', 'common', 'sv')
        for m in rm:
            write_hdl_regmap(f_, rm[m]['subregmap'], m)

    chdir(call_dir)
