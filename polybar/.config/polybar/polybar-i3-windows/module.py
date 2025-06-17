#! /usr/bin/python3

import os
import asyncio
import getpass
import i3ipc
import platform

from icon_resolver import IconResolver

#: Max length of single window title
MAX_LENGTH = 30
#: Base 1 index of the font that should be used for icons
ICON_FONT = 1

HOSTNAME = platform.node()
USER = getpass.getuser()

ICONS = [
    ('class=org.mozilla.firefox', ''),
    ('class=firefox', ''),
    ('class=Code', ''),
    ('class=code-oss-dev', ''),
    ('class=Alacritty', ''),
    ('class=ter', '󰑕'),
    ('class=lzgit', ''),
    ('*', ''),
]

FORMATERS = {
    'Google-chrome': lambda title: title.replace(' - Google Chrome', ''),
    'org.mozilla.firefox': lambda title: title.replace(' — Mozilla Firefox', ''),
    'firefox': lambda title: title.replace(' — Mozilla Firefox', ''),
    'Alacritty': lambda title: title.replace(f'{USER}@{HOSTNAME}:', ''),
    'ter': lambda title: title.replace(f'{USER}@{HOSTNAME}:', ''),
    'Code': lambda title: title.replace(' - Visual Studio Code', ''),
    'lzgit': lambda title: 'lazygit',
}

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
COMMAND_PATH = os.path.join(SCRIPT_DIR, 'command.py')

icon_resolver = IconResolver(ICONS)


def main():
    i3 = i3ipc.Connection()

    i3.on('workspace::focus', on_change)
    i3.on('window::focus', on_change)
    i3.on('window', on_change)

    loop = asyncio.get_event_loop()

    loop.run_in_executor(None, i3.main)

    render_apps(i3)

    loop.run_forever()


def on_change(i3, e):
    render_apps(i3)

def find_output(tree, output_name):
    for con in tree.descendants():
        if con.type == 'output' and con.name == output_name:
            return con
    return None

def find_displayed_workspace(output):
    for con in output.descendants():
        if con.type == 'workspace' and con.fullscreen_mode == 1:
            return con
    return None

def get_apps(i3):
    tree = i3.get_tree()
    if 'MONITOR' in os.environ:
        return find_displayed_workspace(find_output(tree, os.environ['MONITOR'])).leaves()
    else:
        return tree.find_focused().workspace().leaves()


def render_apps(i3):

    apps = [app for app in get_apps(i3) if app.name is not None]

    out = '%{O12}%{F#89b4fa}|%{O12}%{F-}'.join(format_entry(app) for app in apps)

    print(out, flush=True)


def format_entry(app):
    title =  make_title(app)
    u_color = '#89b4fa' if app.focused else '#e84f4f' if app.urgent else None
    if u_color:
        return F'%{{U{u_color}}}%{{+u}} {title} %{{-u}}'
    else:
        return F' {title} '


def make_title(app):
    out = get_prefix(app) + format_title(app)

    if app.focused:
        out = '%{F#89b4fa}' + out + '%{F-}'

    return f'%{{A1:{COMMAND_PATH} {app.id} focus:}}%{{A2:{COMMAND_PATH} {app.id} kill:}}{out}%{{A}}%{{A}}'


def get_prefix(app):
    icon = icon_resolver.resolve({
        'class': app.window_class,
        'name': app.name,
    })
    return f'%{{T{ICON_FONT}}}{icon} %{{T-}}'


def format_title(app):
    klass = app.window_class
    name = app.name

    title = FORMATERS[klass](name) if klass in FORMATERS else name

    if len(title) > MAX_LENGTH:
        title = title[:MAX_LENGTH - 3] + '...'

    return title

main()
