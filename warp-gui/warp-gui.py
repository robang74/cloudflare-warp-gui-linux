#!/usr/bin/python3
################################################################################
#
# Cloudflare WARP GUI for linux
#
# (C) 2022, Pham Ngoc Son <phamngocsonls@gmail.com> - Public Domain
# (C) 2024, Roberto A. Foglietta <roberto.foglietta@gmail.com> - 3-clause BSD
# (C) 2024, Pham Ngoc Son <phamngocsonls@gmail.com> - 3-clause BSD
# (C) 2024, Roberto A. Foglietta <roberto.foglietta@gmail.com> - GPLv2
# (C) 2025, Roberto A. Foglietta <roberto.foglietta@gmail.com> - GPLv2
#
################################################################################
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# https://www.gnu.org/licenses/old-licenses/gpl-2.0.en.html
#
# NO WARRANTY ##################################################################
# 
# 11. BECAUSE THE PROGRAM IS LICENSED FREE OF CHARGE, THERE IS NO WARRANTY FOR
# THE PROGRAM, TO THE EXTENT PERMITTED BY APPLICABLE LAW. EXCEPT WHEN OTHERWISE
# STATED IN WRITING THE COPYRIGHT HOLDERS AND/OR OTHER PARTIES PROVIDE THE
# PROGRAM "AS IS" WITHOUT WARRANTY OF ANY KIND, EITHER EXPRESSED OR IMPLIED,
# INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
# FITNESS FOR A PARTICULAR PURPOSE. THE ENTIRE RISK AS TO THE QUALITY AND
# PERFORMANCE OF THE PROGRAM IS WITH YOU. SHOULD THE PROGRAM PROVE DEFECTIVE,
# YOU ASSUME THE COST OF ALL NECESSARY SERVICING, REPAIR OR CORRECTION.
#
# 12. IN NO EVENT UNLESS REQUIRED BY APPLICABLE LAW OR AGREED TO IN WRITING WILL
# ANY COPYRIGHT HOLDER, OR ANY OTHER PARTY WHO MAY MODIFY AND/OR REDISTRIBUTE
# THE PROGRAM AS PERMITTED ABOVE, BE LIABLE TO YOU FOR DAMAGES, INCLUDING ANY
# GENERAL, SPECIAL, INCIDENTAL OR CONSEQUENTIAL DAMAGES ARISING OUT OF THE USE
# OR INABILITY TO USE THE PROGRAM (INCLUDING BUT NOT LIMITED TO LOSS OF DATA OR
# DATA BEING RENDERED INACCURATE OR LOSSES SUSTAINED BY YOU OR THIRD PARTIES OR
# A FAILURE OF THE PROGRAM TO OPERATE WITH ANY OTHER PROGRAMS), EVEN IF SUCH
# HOLDER OR OTHER PARTY HAS BEEN ADVISED OF THE POSSIBILITY OF SUCH DAMAGES.
#
################################################################################
# To check the WARP connection: curl https://www.cloudflare.com/cdn-cgi/trace/

import signal
import atexit
import subprocess

from tkinter import *
from warp_gui.actions import *

# create root windows ##########################################################

bgcolor = "GainsBoro"
root = Tk()

on_dir = dir_path + "/free/slide-on.png"
on = PhotoImage(file = on_dir)

off_dir = dir_path + "/free/slide-off.png"
off = PhotoImage(file = off_dir)

try:
    logo_dir = dir_path + "/orig/team-logo.png"
    tmlogo = PhotoImage(file = logo_dir)
except:
    logo_dir = dir_path + "/free/team-letter.png"
    tmlogo = PhotoImage(file = logo_dir)

try:
    cflogo_dir = dir_path + "/orig/warp-logo.png"
    cflogo = PhotoImage(file = cflogo_dir)
except:
    cflogo_dir = dir_path + "/free/warp-letter.png"
    cflogo = PhotoImage(file = cflogo_dir)

try:
    appicon_path = dir_path + "/orig/appicon-init.png"
    appicon_init = PhotoImage(file = appicon_path)
except:
    appicon_path = dir_path + "/free/appclou-init.png"
    appicon_init = PhotoImage(file = appicon_path)

try:
    appicon_path = dir_path + "/orig/appicon-pass.png"
    appicon_pass = PhotoImage(file = appicon_path)
except:
    appicon_path = dir_path + "/free/appclou-pass.png"
    appicon_pass = PhotoImage(file = appicon_path)

try:
    appicon_path = dir_path + "/orig/appicon-warp.png"
    appicon_warp = PhotoImage(file = appicon_path)
except:
    appicon_path = dir_path + "/free/appclou-warp.png"
    appicon_warp = PhotoImage(file = appicon_path)

try:
    appicon_path = dir_path + "/orig/appicon-team.png"
    appicon_team = PhotoImage(file = appicon_path)
except:
    appicon_path = dir_path + "/free/appclou-team.png"
    appicon_team = PhotoImage(file = appicon_path)

# root window background color, title, dimension and position
root.title("WARP GUI")
root.geometry("360x480+120+90")
root.resizable(False,False)
root.iconphoto(True,appicon_init)
root.config(bg = bgcolor)

menubar = Menu(root, bg = bgcolor, activeborderwidth = 4, relief=GROOVE, fg = "Black")

def create_cascade_menu(menubar=menubar):
    cm = Menu(menubar, tearoff=1, font = "Arial 12", title="WARP GUI > MENU")
    cm.add_command(label=" \u204E WARP Session Renew ", command=session_renew)
    cm.add_command(label=" \u204E WARP Session Delete", command=registration_delete)
    cm.add_command(label=" \u204E WARP Settings Reset", command=settings_reset)
    cm.add_command(label=" \u204E WARP Service Restart", command=service_restart)
    cm.add_separator()
    cm.add_command(label="\u2058 DNS Filter: family",   command=partial(set_dns_filter, "full"))
    cm.add_command(label="\u2058 DNS Filter: malware",  command=partial(set_dns_filter, "malware"))
    cm.add_separator()
    cm.add_command(label=" \u2022 WARP Mode: doh",      command=partial(set_mode, "doh"))
    cm.add_command(label=" \u2022 WARP Mode: warp",     command=partial(set_mode, "warp"))
    cm.add_command(label=" \u2022 WARP Mode: warp+doh", command=partial(set_mode, "warp+doh"))
    cm.add_command(label=" \u2022 WARP Mode: tunnel",   command=partial(set_mode, "tunnel_only"))
    cm.add_command(label=" \u2022 WARP Mode: proxy",    command=partial(set_mode, "proxy"))
    cm.add_separator()
    cm.add_command(label="\u21C5 Service Taskbar Icon", command=service_taskbar)
    cm.add_command(label="\u21BA Refresh Information",  command=information_refresh)
    cm.add_separator()
    cm.add_command(label="\u24D8 GUI App Information",  command="", state=DISABLED)
    cm.add_command(label="\u24E7 GUI App Termination",  command=kill_all_instances)
    cm.add_separator()
    return cm

helpmenu = create_cascade_menu()

def add_vertical_separator(text="", menubar=menubar):
    if not text:
        text="\u205D"
    menubar.add_command(label=text, compound="left", state=DISABLED)

menubar.add_cascade(label="\u25BD MENU", compound="left", menu=helpmenu)
add_vertical_separator()
menubar.add_command(label="\u21F1 IP \u21F2",
    command=ipaddr_info_update, compound="left", state=DISABLED)
add_vertical_separator()
menubar.add_command(label=dl_get_uchar() + " TOP",
    command=topmost_toggle, compound="left")
add_vertical_separator(" -=- ")
menubar.add_command(label="\u2991\u2600\u26a1\u2602\u2992",
    command=show_weather_xterm, compound="right", state=DISABLED)

# Access information
acc_label = Label(root, text = "", bg = bgcolor, font = ("Arial", 40, 'bold'))
acc_label.pack(pady = 0)

version = cf_info()
if version.find("not found") > -1:
    warp_version = "WARP not found"
else:
    warp_version = version
warpver_label = Label(root, text = warp_version, fg = "DimGray",
    bg = bgcolor, font = ("Arial", 12))
warpver_label.pack(pady = (0,10))

# IP information
ipaddr_label = Label(root, fg = "MidNightBlue", bg = bgcolor,
    font = ("Arial", 14), text = "\n" + ipaddr_searching)
ipaddr_label.pack(pady = (20,25))

# Create A Button
on_button = Button(root, image = off, bd = 0, relief=FLAT,
    activebackground = bgcolor, bg = bgcolor)
if get_status() == "UP":
    on_button.config(image = on)
else:
    ipaddr_label.config(fg = "DimGray")

################################################################################

acc_info_update_thread = Thread(target=acc_info_update)
acc_info_update_thread.start()

on_button.config(command = slide_switch, state = DISABLED)
on_button.pack(pady = 0)

status_label = Label(root, text = "", fg = "Black", bg = bgcolor, font = ("Arial", 15))
status_label.pack(padx=0, pady=(0,10))

stats_label = Label(root, text = "", bg = bgcolor, font = ("Courier Condensed", 10))
stats_label.pack(padx=10, pady=(10,10))

################################################################################

def slide_update(status):
    if status == slide_update.status_old:
        return
    slide_update.status_old = status
    slide = off

    if status == "UP":
        status_label.config(text = "Connected", fg = "Blue",
            font = ("Arial", 15, 'bold') )
        slide = on
    elif status == "DN":
        status_label.config(text = "Disconnected", fg = "DimGray",
            font = ("Arial", 15, '') )
        stats_label.config(fg = "DimGray")
    elif status == "RGM":
        status_label.config(text = "No registration", fg = "DimGray",
            font = ("Arial", 15, '') )
    elif status == "CN":
        status_label.config(text = "Connecting...", fg = "DimGray",
            font = ("Arial", 15, 'italic') )
    elif status == "DC":
        status_label.config(text = "Disconnecting...", fg = "DimGray",
            font = ("Arial", 15, 'italic') )
    elif status == "ERR":
        status_label.config(fg = "DimGray", font = ("Arial", 15, 'italic') )

    on_button.config(image = slide)

slide_update.status_old = ""

def stats_label_update():
    if stats_label_update.inrun:
        return
    stats_label_update.inrun = 1

    warp_stats = subprocess.run("warp-cli tunnel stats", shell=True, capture_output=True, text=True).stdout
    if warp_stats == "":
        pass
    elif warp_stats != stats_label_update.warp_stats_last:
        stats_label_update.warp_stats_last = warp_stats
        wsl = warp_stats.replace(';',' ')
        wsl = wsl.splitlines()
        wsl = wsl[0] + "\n" + "\n".join(map(str, wsl[2:]))
        stats_label.config(text = wsl, fg = "MidNightBlue")

    stats_label_update.inrun = 0

stats_label_update.warp_stats_last = ""
stats_label_update.inrun = 0

################################################################################

frame = Frame(root, bg = bgcolor)
frame.pack(side=BOTTOM, fill=X)

gui_pid_str = "pid:" + str(getpid())

lbl_pid_num = Label(frame, text = gui_pid_str, fg = "DimGray", bg = bgcolor,
    font = ("Arial", 10), pady=10, padx=10, justify=LEFT)
lbl_pid_num.place(relx=0.0, rely=1.0, anchor='sw')

gui_version_str = "GUI v0.8.9"

lbl_gui_ver = Label(frame, text = gui_version_str, fg = "DimGray", bg = bgcolor,
    font = ("Arial", 11, 'bold'), pady=0, padx=10, justify=LEFT)
lbl_gui_ver.place(relx=0.0, rely=0.67, anchor='sw')

slogan = Button(frame, image = "", command=enroll)
slogan.pack(side=BOTTOM, pady=10, padx=(10,10))
access_icon_update()

lbl_setting = Label(frame, text = "mode: - - - -\ndnsf: - - - -", fg = "Black",
    bg = bgcolor, font =  ("Courier", 10), pady=10, padx=10, justify=LEFT)
lbl_setting.place(relx=1.0, rely=1.0, anchor='se')

################################################################################

atexit.register(handle_exit)
signal.signal(signal.SIGTERM, handle_exit)

# this should be setup before calling main loop
signal.signal(signal.SIGINT, ctrlc_handler)

# it seems useless w or w/ signal but keep for further investigation
# root.bind_all("<Control-C>", ctrlc_handler)

################################################################################

unexpose_handler.inrun = 0
unexpose_handler.dbg = 0

helpmenu.bind_all("<FocusOut>", unexpose_handler)

################################################################################

root.config(menu=menubar)
root.tr = UpdateThread()
root.update_idletasks()
root.mainloop()
kill_weather_xterm()
try: root.destroy()
except: pass
