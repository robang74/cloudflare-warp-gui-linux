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

from tkinter import *
from os import getpid, path, kill, environ
from requests import get as getUrl, urllib3
from time import process_time_ns, monotonic, sleep
from socket import getaddrinfo, AF_INET, AF_INET6
from threading import Thread, Event
from random import randrange, seed
from ipinfo import getHandler
from functools import partial
from sys import _getframe

################################################################################

filename = path.basename(__file__)
dir_path = path.dirname(path.realpath(__file__))
path_bin = "/bin:/usr/bin:/usr/local/bin"
shellbin = "/bin/bash"

registration_new_cmdline = "warp-cli --accept-tos registration new"
registration_new_cmdline +=" && warp-cli dns families malware"
registration_new_cmdline +=" && warp-cli mode warp+doh"

ipv6_system_check_cmdline = 'for i in all.disable_ipv6 default.disable_ipv6;'
ipv6_system_check_cmdline +=' do sysctl net.ipv6.conf.$i; done | grep "= *0"'
ipv6_system_check_cmdline +=' | wc -l'

show_weather_xterm_title = "Weekly Weather Forecast"
strn =  'xterm -bg black +wf -hold +ls -fa "Ubuntu Mono" -fs 12 -uc +ah +bc +aw'
strn +=f' -geometry "130x40+500+90" -title "{show_weather_xterm_title}"  +l +cm'
strn += ' -e ${SHELL} -c "echo; echo \ Weather report: ${city} loading...; curl'
strn += ' -qsNm 5 wttr.in/${city}?Fp 2>&1 | sed -e \'\$d\'; printf \033[?25l\a"'
show_weather_xterm_cmdline = strn + ' >/dev/null 2>&1 & echo $!'

ipaddr_errstring = "\n-= error or timeout =-"
ipaddr_searching = "-=-.-=-.-=-.-=-"

def T_POLLING(): return 0.10

# for current func name, specify 0 or no argument.
# for name of caller of current func, specify 1.
# for name of caller of caller of current func, specify 2. etc.
func_name = lambda n=0: _getframe(n+1).f_code.co_name

_dbg_print = lambda *p: _chk_print("DBG", *p)
_wrn_print = lambda *p: _chk_print("WRN", *p)
_err_print = lambda *p: _chk_print("ERR", *p)

def _chk_print(sn, *p):
    fn=func_name(2)
    if sn != "DBG" or eval(fn+'.dbg'):
        print(f"{sn}> {fn}:", *p)

''' OLDER IMPLEMENTATION EQUIVALENT, FOR DEBUG

from subprocess import getoutput
def cmdoutput(cmd):
    return getoutput(cmd)
'''
''' NEWER IMPLEMENTATION EQUIVALENT, FOR DEFAULT
'''
from subprocess import run as cmdrun
def cmdoutput(cmd):
    proc = cmdrun(cmd, shell=True, capture_output=True, text=True,
        env={"PATH": path_bin}, encoding='utf-8')
    combined_output = proc.stdout + proc.stderr
    lines = combined_output.splitlines()
    non_blank_lines = [line for line in lines if line.strip()]
    clean_output = '\n'.join(non_blank_lines)
    return clean_output

################################################################################

''' TO APPEND AFETR A FUNCTION

the_function_name.dict = dict()
#
# dictionary caching delay value:
#   -N = perment cache (no reset)
#    0 = no any cache (disabled)
#    N = cache reset (delayed)
#
the_function_name.delay = 600 # value in seconds
the_function_name.reset = the_function_name.delay

'''

def try_dict_get(key):
    func = eval(func_name(1))
    if func.delay:
        try:
            value = func.dict[key]
            return value
        except:
            pass
    return None


def rst_dict_set(key, val):
    func = eval(func_name(1))
    if func.reset > 0:
        root.after(func.delay << 10, partial(fnc_dict_rst, func))
        func.reset = 0
    func.dict[key] = val


def fnc_dict_rst(func):
    func.dict = dict()
    func.reset = func.delay

################################################################################

def inet_get_ipaddr_info(weburl="ifconfig.me", ipv6=False):
    self = inet_get_ipaddr_info

    weburl = weburl.split('/',1)
    dmname = weburl[0]
    url = ""

    keydct = ("ipv6:" if ipv6 else "ipv4:") + dmname
    restrn = try_dict_get(keydct)
    if restrn != None:
        return restrn

    self.dbg = inet_get_ipaddr_info.dbg or get_ipaddr_info.dbg

    if ipv6:
        # Resolve to an IPv6 address only (family=AF_INET6)
        ip_info = getaddrinfo(dmname, 80, family=AF_INET6)
        # Construct the URL using the IPv6 address
        # IPv6 addresses should be enclosed in []
        ip_address = ip_info[0][4][0]
        url = f"http://[{ip_address}]/"
    else:
        # Resolve to an IPv4 address only (family=AF_INET)
        ip_info = getaddrinfo(dmname, 80, family=AF_INET)
        # Construct the URL using the IPv4 address
        ip_address = ip_info[0][4][0]
        url = f"http://{ip_address}/"

    if len(weburl) > 1:
        url+= weburl[1]

    _dbg_print(f"web = {weburl}, url = {url}")

    # Send the GET request with the Host header set to the original domain
    try:
        res = getUrl(url, headers={"Host": dmname}, timeout=(1.5,2.0))
    except Exception as e:
        raise(e)

    if res.status_code != 200:
        _wrn_print("return code =", res.status_code)

    # RAF: return code 206 is partial content and should be discarded
    if res.status_code == 206:
        return ""

    restrn = res.text.split('\n',1)[0]
    rst_dict_set(keydct, restrn)
    return restrn

inet_get_ipaddr_info.dict = dict()
#
# dictionary caching delay value:
#   -N = perment cache (no reset)
#    0 = no any cache (disabled)
#    N = cache reset (delayed)
#
inet_get_ipaddr_info.delay = 600 # value in seconds
inet_get_ipaddr_info.reset = inet_get_ipaddr_info.delay
inet_get_ipaddr_info.dbg = 0


def ipv4_get_ipaddr_info(url="ifconfig.me"):
    return inet_get_ipaddr_info(url, 0)

def ipv6_get_ipaddr_info(url="ifconfig.me"):
    return inet_get_ipaddr_info(url, 1)

################################################################################

# RAF, TODO
#
# This lock mechanism is based on a non atomic check-and-set opration in the
# future it can be changed using the 'with lock' paradigm and involving a
# threading.Lock(). However, there is no any race condition here to address but
# just a operational serialisation just for optimisation. Hence a flag is ok.
#
##  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #

def inrun_wait_or_set(wait=0):
    func = eval(func_name(1))
    if wait > 0:
        sleep(wait)
    else:
        while func.inrun:
            sleep(T_POLLING())
    func.inrun = 1


def inrun_reset(val=None):
    func = eval(func_name(1))
    func.inrun = 0
    return val

##  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #

is_status_stable = lambda x: (x == "UP" or x == "DN")

is_network_down = lambda x: (x == "RGM" or x == "ERR")

def get_status(wait=0):
    inrun_wait_or_set(wait)

    status = cmdoutput("warp-cli status")
    _dbg_print("(b)", status.replace("\n", " "))
    if not status.find("Success"):
        return get_status(0.5)

    status = status.split("\n")[0]
    status_err = status.split(".")
    get_status.err = "\n".join(status_err)

    if status.find("Disconnected") > -1:
        status = "DN"
    elif status.find("Connected") > -1:
        status = "UP"
    elif status.find("Connecting") > -1:
        status = "CN"
    elif status.find("Registration Missing") > -1:
        status = "RGM"
    else:
        status = "ERR"

    if status != get_status.last:
        get_ipaddr_info.text = ""
        get_status.last = status

    _dbg_print("(e)", status, status_err)
    return inrun_reset(status)

get_status.err = ""
get_status.last = ""
get_status.inrun = 0
get_status.dbg = 0

################################################################################

def update_guiview_by_menu(info_str, err_str=""):
    if err_str != "":
        err_str = err_str.split("\n")
        if err_str[0] == "Success":
            err_str = err_str[0] + ": " + info_str
        else:
            err_str = err_str[0].split(".")
            err_str = "\n".join(err_str)
        if not info_str:
            info_str = err_str

    stats_label.config(text = err_str, fg = "OrangeRed")

    root.tr.resume()
    update_guiview(get_status(), 0, 1)


def common_reset_by_menu(refresh=False):
    root.tr.pause()
    stats_label.config(text = "")
    if not refresh:
        if get_status.last != "DN":
            slide_update("DC")
        get_status.last = "RGM"
        get_access.last = ""
        status_icon_update()
        access_icon_update()
    ipaddr_text_set()


def service_restart():
    enroll.team = 0
    common_reset_by_menu()
    err_str = cmdoutput("pkexec systemctl restart warp-svc")
    update_guiview_by_menu("service restart", err_str)


def settings_reset():
    enroll.team = 0
    common_reset_by_menu()
    err_str = cmdoutput("warp-cli settings reset")
    update_guiview_by_menu("settings reset", err_str)


def registration_delete():
    enroll.team = 0
    common_reset_by_menu()
    err_str = cmdoutput("warp-cli registration delete")
    update_guiview_by_menu("registration delete", err_str)


def information_refresh():
    kill_weather_xterm()
    common_reset_by_menu(True)
    fnc_dict_rst(inet_get_ipaddr_info)
    fnc_dict_rst(get_country_city)
    update_guiview_by_menu("information refresh")


def set_slogan_button_state(state):
    slogan.config(state = state)
    slogan.update_idletasks()

def session_renew():
    global registration_new_cmdline

    set_slogan_button_state(DISABLED)
    warp_mode_old = get_settings.warp_mode
    warp_dnsf_old = get_settings.warp_dnsf
    oldval = get_status.last
    common_reset_by_menu()

    if get_settings.warp_mode == 0 or get_settings.warp_dnsf == 0:
        get_settings()
    if get_status.last == "":
        get_status()

    cmdline = registration_new_cmdline
    if oldval == "UP":
        cmdline += " && warp-cli connect"

    err_str = cmdoutput("warp-cli registration delete; " + cmdline)
    if oldval == "UP":
        get_status.last = "CN"
    else:
        get_status.last = "DN"

    set_settings(warp_mode_old, warp_dnsf_old)
    update_guiview_by_menu("WARP session renew", err_str)
    access_icon_update()
    set_slogan_button_state(NORMAL)

################################################################################

def get_access():
    inrun_wait_or_set()

    account = cmdoutput("warp-cli registration show")
    get_access.last = (account.find("Team") > -1)

    return inrun_reset(get_access.last)

get_access.last = ""
get_access.inrun = 0


def access_icon_update(status=get_status.last, zerotrust=get_access.last):
    enroll.team = 1
    if zerotrust:
        slogan.config(image = tmlogo)
    elif is_network_down(status) or not status:
        slogan.config(image = cflogo)
        enroll.team = 0
    else:
        slogan.config(image = tmlogo)

def acc_info_update():
    status = get_status.last
    zerotrust = get_access()

    if zerotrust == True:
        acc_label.config(text = "Zero Trust", fg = "Blue")
    else:
        acc_label.config(text = "WARP", fg = "Tomato")

    access_icon_update(status, zerotrust)
    status_icon_update(status, zerotrust)


def status_icon_update(status=get_status.last, zerotrust=get_access.last):
    if zerotrust:
        if status == "UP":
            root.iconphoto(False,appicon_team)
        else:
            root.iconphoto(False,appicon_pass)
    else:
        if status == "UP":
            root.iconphoto(False,appicon_warp)
        else:
            root.iconphoto(False,appicon_pass)


def cf_info():
    return cmdoutput("warp-cli --version")


def ipaddr_info_update(enable=0):

    def force_get_ipaddr_info():
        ipaddr_text_set()
        text = get_ipaddr_info(True)
        change_ipaddr_text(text)

    if get_ipaddr_info.dbg:
        print("ipaddr_info_update: ", enable)

    if enable:
        try:
            if get_ipaddr_info.dbg:
                print("ipaddr_info_update thread", str(ipaddr_info_update.tr))
            if ipaddr_info_update.tr != None:
                ipaddr_info_update.tr.join()
        except:
            pass
        menubar.entryconfigure(3, state = NORMAL)
        inrun_reset()
    else:
        inrun_wait_or_set()
        menubar.entryconfigure(3, state = DISABLED)
        root.tr.daemon_start(target=force_get_ipaddr_info)

ipaddr_info_update.tr = None
ipaddr_info_update.inrun = 0

################################################################################

seed(process_time_ns())

def get_ipaddr_info(force=False):
    global ipaddr_searching, ipaddr_errstring
    self = get_ipaddr_info

    inrun_wait_or_set()

    self.dbg = inet_get_ipaddr_info.dbg or get_ipaddr_info.dbg

    _dbg_print(f"{self.tries} -", self.text.replace("\n", " "), "-",
        str(int((monotonic()-self.start)*1000))+" ms" if self.start else "")
    if self.dbg: self.start = monotonic()

    if force or self.text == "":
        self.tries = 0
    elif self.city.find("(") < 0:
        pass
    elif self.ipv4 or self.ipv6:
        return inrun_reset(self.text)

    self.tries += 1
    url4 = self.wurl4[0]
    self.wurl4 = self.wurl4[1:] + self.wurl4[:1]
    url6 = self.wurl6[0]
    self.wurl6 = self.wurl6[1:] + self.wurl6[:1]

    if self.dbg and self.tries == 1:
        print("ipv4 urls:", url4)
        print("ipv6 urls:", url6)

    ipv4 = ipv6 = ""
    try:
        ipv4 = ipv4_get_ipaddr_info(url4)
        self.ipv4 = ipv4
    except Exception as e:
        if 1 or self.dbg:
            _err_print(f"ipv4, {self.tries}, {url4} - ", str(e))
        self.ipv4 = ""
    try:
        ipv6 = ipv6_get_ipaddr_info(url6)
        self.ipv6 = ipv6
    except Exception as e:
        if 1 or self.dbg:
            _err_print(f"ipv6, {self.tries}, {url6} - ", str(e))
        self.ipv6 = ""

    if not ipv4 and not ipv6:
        if self.dbg:
            _wrn_print("ipaddr quest failed, but still trying")
        return inrun_reset(ipaddr_searching + ipaddr_errstring)

    self.city = get_country_city(ipv4 if ipv4 else ipv6)
    self.text = ipv4 + (" - " if ipv4 else "") + self.city \
            + "\n" + (ipv6 if ipv6 else "-= ipv6 address missing =-")

    _dbg_print(f"{self.tries} -", self.text.replace("\n", " "), "-" +
        str(int((monotonic()-self.start) * 1000)) + "ms" if self.start else "")

    ipaddr_info_update(1)

    return inrun_reset(self.text)

get_ipaddr_info.hadler_token = ""
get_ipaddr_info.handler = getHandler(get_ipaddr_info.hadler_token)
get_ipaddr_info.wurls = ['ifconfig.me/ip', 'icanhazip.com', 'myip.wtf/text', 'eth0.me']
get_ipaddr_info.wurl6 = ['api6.ipify.org/','ip6only.me/ip/'] + get_ipaddr_info.wurls
get_ipaddr_info.wurl4 = ['api.ipify.org/', 'ip4.me/ip/'] + get_ipaddr_info.wurls
get_ipaddr_info.inrun = 0
get_ipaddr_info.start = 0
get_ipaddr_info.text = ""
get_ipaddr_info.ipv4 = ""
get_ipaddr_info.ipv6 = ""
get_ipaddr_info.city = ""
get_ipaddr_info.tries = 0
get_ipaddr_info.dbg = 0


def get_country_city(ipaddr):
    global ipaddr_errstring
    self = get_country_city

    if ipaddr == "":
        return ""

    strn = try_dict_get(ipaddr)
    if strn != None:
        if not self.city:
            self.city = self.last
        return strn

    try:
        # using the access_token from ipinfo
        details = get_ipaddr_info.handler.getDetails(ipaddr, timeout=(0.5,1.0))
    except:
        return ipaddr_errstring

    self.city = details.city
    if self.city != self.last:
        kill_weather_xterm()
    self.last = self.city

    strn = details.city + " (" + details.country + ")"
    rst_dict_set(ipaddr, strn)

    _dbg_print("dict =", self.dict)
    return strn

get_country_city.city = ""
get_country_city.last = ""
get_country_city.dict = dict()
#
# geolocalization caching delay value:
#   -N = perment cache (no reset)
#    0 = no any cache (disabled)
#    N = cache reset (delayed)
#
get_country_city.delay = 600 # value in seconds
get_country_city.reset = get_country_city.delay
get_country_city.dbg = get_ipaddr_info.dbg


def ipv6_system_check():
    retstr = cmdoutput(ipv6_system_check_cmdline)
    ipv6_system_check.enabled = (retstr == '2')

ipv6_system_check.enabled = -1


ipv6_system_check_thread = Thread(target=ipv6_system_check)
ipv6_system_check_thread.start()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def enroll():
    global registration_new_cmdline
    slogan.config(state = DISABLED)

    if not enroll.team:
        output = cmdoutput(registration_new_cmdline)
        if output.find("success"):
            enroll.team = 1
    else:
        organization = simpledialog.askstring(title="Organization",
                                  prompt="What's your Organization?:")
        if organization:
            print("enroll in TEAM network:", organization)
            new_command = "warp-cli registration delete; "
            new_command+= "yes yes | warp-cli --accept-tos teams-enroll "
            output = cmdoutput(new_command + organization)
            print("enroll in TEAM returns:", output)

    auto_update_guiview()
    slogan.config(state = NORMAL)

enroll.team = 0


def set_dns_filter(filter):
    out = cmdoutput("warp-cli dns families " + filter)
    get_settings.warp_settings = ""


def set_mode(mode):
    out = cmdoutput("warp-cli mode " + mode)
    get_settings.warp_settings = ""
    ipaddr_text_set()


def service_taskbar():
    cmdline = 'systemctl --user status warp-taskbar | sed -ne "s/Active: //p"'
    retstr = cmdoutput(cmdline)
    if retstr.find("inactive") > -1:
        cmdline = 'systemctl --user enable warp-taskbar;'
        cmdline+=' systemctl --user start warp-taskbar'
    else:
        cmdline = 'systemctl --user disable warp-taskbar;'
        cmdline+=' systemctl --user stop warp-taskbar'
    retstr = cmdoutput(cmdline)
    sleep(1)


def set_weather_button_state(state):
    if state == "update":
        state = (show_weather_xterm.pid < 0)
    elif state:
        show_weather_xterm.pid = -1
    menubar.entryconfigure(7, state=(NORMAL if state else DISABLED))


def set_on_button_state(state):
    on_button.config(state = state)
    on_button.update_idletasks()


def change_ipaddr_text(text=""):
    if not text:
        text = get_ipaddr_info()
    if text != ipaddr_label.cget("text"):
        ipaddr_text_set(text)
        set_weather_button_state("update")
        set_on_button_state(NORMAL)

def auto_update_guiview(errlog=1):
    status = get_status()
    stats_label.config(text = get_status.err)
    while status == "CN" or status == "DC":
        sleep(T_POLLING())
        status = get_status()
        #print("status:", status)
    update_guiview(status, errlog, 1)


def update_guiview(status, errlog=1, force=0):
    self = update_guiview
    if self.inrun:
        return
    self.inrun = 1

    stats_err = 0
    if errlog and get_status.err != "":
        stats_label.config(text = get_status.err, fg = "OrangeRed")
        stats_err = 1

    if status != self.status_old or force:
        self.status_old = status

        if status == "UP":
            on_button.config(image = on)
        elif status != "CN":
            on_button.config(image = off)
            if errlog and stats_err == 0:
                stats_label.config(fg = "DimGray")
        slide_update(status)

        if is_status_stable(status):
            root.tr.pause()
            root.tr.daemon_start(target=acc_info_update)
            root.tr.daemon_start(target=change_ipaddr_text)
            root.tr.daemon_start(target=get_settings)
            root.tr.resume()
            sleep(T_POLLING())

    self.inrun = 0

update_guiview.inrun = 0
update_guiview.status_old = 1


def ipaddr_text_set(ipaddr_text=ipaddr_searching):
    if ipaddr_text == ipaddr_searching:
        ipaddr_text = "\n" + ipaddr_searching
        set_weather_button_state(0)
        get_country_city.city = ""
    fgcolor = "MidNightBlue" if get_status.last == "UP" else "DimGray"
    ipaddr_label.config(fg = fgcolor)
    ipaddr_label.config(text = ipaddr_text)
    ipaddr_label.update_idletasks()


def slide_switch():
    if slide_switch.inrun:
        return
    slide_switch.inrun = 1

    root.tr.pause()
    ipaddr_text_set()
    set_on_button_state(DISABLED)

    if get_status.last == "UP":
        get_status.last = "DC"
        status_label.config(text = "Disconnecting...", fg = "Dimgray",
            font = ("Arial", 15, 'italic') )
        retstr = cmdoutput("warp-cli disconnect")
    elif get_status.last == "DN":
        get_status.last = "CN"
        status_label.config(text = "Connecting...", fg = "Dimgray",
            font = ("Arial", 15, 'italic') )
        retstr = cmdoutput("warp-cli --accept-tos connect")

    root.tr.resume()
    auto_update_guiview()
    slide_switch.inrun = 0

slide_switch.inrun = 0


def kill_all_instances(filename=filename):
    global show_weather_xterm_title

    if not filename:
        handle_exit()

    ereg = '"s/\([0-9]*\) .*python.*[ /]' + filename + '$/\\\\1/p"'
    cmda = 'pgrep -u $USER -alf ' + filename + ' | sed -ne ' \
          + ereg + " | grep -v $PPID"

    ereg = '"s/\([ 0-9]*\) .*title ' + show_weather_xterm_title + ' .*/\\\\1/p"'
    cmdx = 'pgrep -u $USER -alf xterm | sed -ne ' + ereg

    self = kill_all_instances
    ret_str = ""
    try:
        ret_str = cmdoutput(f"for i in $({cmdx}); do kill $i; kill -1 $i; done")
    except Exception as e:
        _err_print("xterm - ", str(e), "\n\n")
    else:
        pass
    try:
        ret_str+= cmdoutput(f"for i in $({cmda}); do kill $i; kill -1 $i; done")
    except Exception as e:
        _err_print("guiapp - ", str(e), "\n\n")
    else:
        pass
    if not ret_str: ret_str = "(OK)"
    print(f"kill_all_instances:\n  {cmdx}\n  {cmda}\nreturns: {ret_str}\n")

    handle_exit()


def dl_get_uchar(idx=-1):
    if idx < 0:
        idx = dl_get_uchar.idx + 1
    if idx >= 2 * len(dl_get_uchar.list):
        idx = 0
    dl_get_uchar.idx = idx
    return dl_get_uchar.list[int(idx/2)][int(idx%2)]

dl_get_uchar.idx = -1
dl_get_uchar.list = [ [ '\u29bf', '\u24ff' ] ]

'''
# RAF: 4th GENERATION ##########################################################
#                 00                      01                      02
        [ '\u29bf', '\u24ff' ], [ '\u272a', '\u24ff' ], [ '\u2732', '\u2731' ] ]


# RAF: 3rd GENERATION ##########################################################

#                 00                      01                      02
        [ '\u24ea', '\u24ff' ], [ '\u24c4', '\u24ff' ], [ '\u24de', '\u24ff' ],
#                 03                      04                      05
        [ '\u29bf', '\u24ff' ], [ '\u29be', '\u29bf' ], [ '\u29bf', '\u272a' ],
#                 06                      07                      08
        [ '\u2b21', '\u2b22' ], [ '\u2729', '\u272a' ], [ '\u2732', '\u2731' ],
#                 09                      10                      11
        [ '\u2662', '\u2666' ], [ '\u2662', '\u2756' ], [ '\u2727', '\u2756' ],
#                 12                      13                      14
        [ '\u2705', '\u2714' ] ]

# RAF: 2nd GENERATION ##########################################################

#                 00                      01                      02
        [ '\u24ea', '\u24ff' ], [ '\u24c4', '\u24ff' ], [ '\u24de', '\u24ff' ],
#                 03                      04                      05
        [ '\u29bf', '\u24ff' ], [ '\u29be', '\u29bf' ], [ '\u2b21', '\u2b22' ],
#                 06                      07                      08
        [ '\u2662', '\u2666' ], [ '\u2705', '\u2714' ], [ '\u2729', '\u272a' ],
#                 09                      10                      11
        [ '\u2727', '\u2756' ], [ '\u2662', '\u2756' ], [ '\u2732', '\u2731' ] ]

# RAF: 1st GENERATION ##########################################################

#                 00                      01                      02
        [ '\u2206', '\u2207' ], [ '\u22bc', '\u22bd' ], [ '\u24ea', '\u24ff' ],
#                 03                      04                      05
        [ '\u24c4', '\u24ff' ], [ '\u24de', '\u24ff' ], [ '\u29bf', '\u24ff' ],
#                 06                      07                      08
        [ '\u25c7', '\u25c6' ], [ '\u25c7', '\u25c8' ], [ '\u2662', '\u2756' ],
#                 09                      10                      11
        [ '\u2662', '\u2666' ], [ '\u2705', '\u2714' ], [ '\u2729', '\u272a' ],
#                 12                      13                      14
        [ '\u2727', '\u2756' ], [ '\u29be', '\u29bf' ], [ '\u29be', '\u2b22' ],
#                 15                      16                      17
        [ '\u2b21', '\u2b22' ], [ '\u25c9', '\u2b24' ], [ '\u2732', '\u2731' ],
#                 18                      19                      20
        [ '\u25ce', '\u25c9' ], ]
'''


def topmost_toggle():
    prev = root.attributes('-topmost')
    root.attributes("-topmost", not prev)
    uc_top = dl_get_uchar()
    set_id = int(dl_get_uchar.idx/2)
    menubar.entryconfigure(5, label=f"{uc_top} TOP")


def kill_weather_xterm(sig=signal.SIGTERM):
    pid = show_weather_xterm.pid
    if not pid > 0:
        return
    try:
        kill(pid, sig)
        kill(pid, signal.SIGINT)
    except:
        pass


def show_weather_xterm():
    global show_weather_xterm_cmdline

    def is_pid_running(pid):
        try:
            kill(pid, 0)
        except OSError:
            return False
        else:
            return True

    def wait_weather_xterm(pid):
        try:
            while is_pid_running(pid):
                sleep(T_POLLING())
            set_weather_button_state(1)
        except:
            return

    set_weather_button_state(0)
    city = get_country_city.city
    if not city:
        return

    self = show_weather_xterm
    city = city.replace(" ", "+")
    if not self.cmdline:
        cmdl = show_weather_xterm_cmdline
        cmdl = cmdl.replace("${city}", city)
        cmdl = cmdl.replace("${SHELL}", shellbin)
        self.cmdline = cmdl
    retstrn = cmdoutput(self.cmdline)
    pid = int(retstrn)
    if pid > 0:
        self.pid = pid
        print(f"{self.__name__}:", city, self.pid)
        root.tr.daemon_start(target=wait_weather_xterm, args=(pid,))
    else:
        self.pid = -1
        _wrn_print("failed with error - ", retstrn)

show_weather_xterm.pid = -1
show_weather_xterm.cmdline = ""

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
tmicon = Label(root, text = "tmlogo", image=tmlogo)
tmicon.image = tmlogo # This creates a persistent reference

try:
    cflogo_dir = dir_path + "/orig/warp-logo.png"
    cflogo = PhotoImage(file = cflogo_dir)
except:
    cflogo_dir = dir_path + "/free/warp-letter.png"
    cflogo = PhotoImage(file = cflogo_dir)
cficon = Label(root, text = "cflogo", image=cflogo)
cficon.image = cflogo # This creates a persistent reference

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

    warp_stats = cmdoutput("warp-cli tunnel stats")
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


class UpdateThread(object):

    def __init__(self, time_ms=1000):
        self.dbg = 0
        self.antm = 0
        self.skip = 0
        self.start = 0
        self.neterr = 0
        self.status = ""
        self.time_ms = time_ms
        self.ltcy_ms = time_ms >> 4
        self.daemon_start(target=self.run)

    def daemon_start(self, *args, **kwargs):
        th = Thread(*args, **kwargs)
        th.daemon = True
        th.start()
        return th

    def pause(self):
        self.skip = 1
        root.update_idletasks()

    def resume(self):
        root.update_idletasks()
        self.skip = 0

    def task(self):
        while self.skip:
            self.start = 0
            sleep(T_POLLING())
            root.update_idletasks()

        start = monotonic()
        dltme = int((start - self.start) * 1000)

        try:
            update = root.attributes('-topmost')
            update|= (root.focus_get() != None)
        except:
            update = 1

        status = get_status()
        neterr = is_network_down(status)
        #print(f"status: {status}, neterr: {neterr}")
        if self.neterr != neterr and status != "CN":
            if self.dbg and self.neterr != "":
                print(f"DBG> network error changed from {self.neterr} to {neterr}")
            self.neterr = neterr
            update = 2

        if update:
            update_guiview(status, 1)
            if status == "UP":
                stats_label_update()
            elif neterr:
                ipaddr_text_set(ipaddr_errstring)
        else:
            stats_label.config(fg = "DimGray")

        if self.status != status and status != "CN":
            if neterr or is_status_stable(status):
                status_icon_update(status, get_access.last)
                if self.dbg:
                    print(f"DBG> status changed '{self.status}' to '{status}' with {neterr}\n")
                root.bell()
            if update > 1:
                slide_update(status)
            self.status = status

        now = monotonic()
        self.antm = int((now - start) * 1000)
        if self.dbg:
            if self.start:
                print("TME> wrk: %4d ms, cyc: %4d ms, dly: %+5d ms" %
                    (self.antm, dltme, dltme - self.time_ms + self.antm))
            else:
                print("TME> wrk: %4d ms, cyc: %4d ms, dly: %+5d ms" %
                    (self.antm, 0, 0))
        self.start = now
        antm = self.antm if self.antm < self.ltcy_ms else self.ltcy_ms
        root.after(self.time_ms - antm, self.task)

    def run(self):
        console_infostart_prints()
        self.task()

################################################################################

frame = Frame(root, bg = bgcolor)
frame.pack(side=BOTTOM, fill=X)

gui_pid_str = "pid:" + str(getpid())

lbl_pid_num = Label(frame, text = gui_pid_str, fg = "DimGray", bg = bgcolor,
    font = ("Arial", 10), pady=10, padx=10, justify=LEFT)
lbl_pid_num.place(relx=0.0, rely=1.0, anchor='sw')

gui_version_str = "GUI v0.9.0"

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

warp_modes = ['unknown', 'warp', 'doh',          'warp+doh',
       'dot',        'warp+dot',           'proxy',     'tunnel_only']
warp_label = [           'Warp', 'DnsOverHttps', 'WarpWithDnsOverHttps',
       'DnsOverTls', 'WarpWithDnsOverTls', 'WarpProxy', 'TunnelOnly' ]
dnsf_types = ['unknown', 'full',   'malware',  'off']
dnsf_label = [           'family', 'security', 'cloudflare-dns' ]

def get_settings():
    global dnsf_types, dnsf_label, warp_label, warp_modes

    retstr = cmdoutput(get_settings.warp_cmdline)
    if get_settings.warp_settings == retstr:
        return

    mode = retstr.find("Mode: ") + 6
    dnsf = retstr.find("Resolve via: ") + 13
    warp_mode_str = retstr[mode:].split()[0]
    warp_dnsf_str = retstr[dnsf:].split()[0].split(".")[0]
    get_settings.warp_settings = retstr

    try:
        get_settings.warp_mode = warp_label.index(warp_mode_str) + 1
    except:
        get_settings.warp_mode = 0

    try:
        get_settings.warp_dnsf = dnsf_label.index(warp_dnsf_str) + 1
    except:
        get_settings.warp_dnsf = 0

    warp_str = warp_modes[get_settings.warp_mode].split("_")[0]
    dnsf_str = dnsf_types[get_settings.warp_dnsf]
    lbl_setting.config(text = "mode:" + warp_str +  "\ndnsf:" + dnsf_str)

get_settings.warp_mode = 0
get_settings.warp_dnsf = 0
get_settings.warp_settings = ""
get_settings.warp_cmdline = 'warp-cli settings | grep --color=never -e "^("'


def settings_report():
    settings_report_cmdline = get_settings.warp_cmdline
    settings_report_cmdline +=' | sed -e "s/.*\\t//" -e "s/@/\\n\\t/"'
    report_str = cmdoutput(settings_report_cmdline)
    print("\n\t-= SETTINGS REPORT =-\n\n" + report_str + "\n")


def set_settings(warp, dnsf):
    global dnsf_types, warp_modes
    set_dns_filter(dnsf_types[dnsf])
    set_mode(warp_modes[warp])

################################################################################

def handle_exit(*args):
    root.quit()
    sleep(5*T_POLLING())
# # # # # # # # # # # # # # # # # #
    kill(getpid(), signal.SIGHUP) #
# RAF: ** WARNING ** # # # # # # #
#
# put 0 instead of getpid() and the x-session will be killed, as well
# this it happens only when the desktop link is used to start the app

atexit.register(handle_exit)
signal.signal(signal.SIGTERM, handle_exit)

def ctrlc_handler(sig, frame):
    print(f' -> {filename} received SIGINT and exiting...\n')
    handle_exit()

# this should be setup before calling main loop
signal.signal(signal.SIGINT, ctrlc_handler)

# it seems useless w or w/ signal but keep for further investigation
# root.bind_all("<Control-C>", ctrlc_handler)

################################################################################

def unexpose_handler(event):
    global helpmenu

    def printdbg(*args):
        if unexpose_handler.dbg:
            return root.after_idle(print,*args)

    printdbg("+-> event:", event, event.widget)

    if not 'helpmenu' in globals():
        printdbg("#1 return \n")
        return
    try:
        if helpmenu == None:
            printdbg("#2 return \n")
            return
    except:
        printdbg("#3 return \n")
        return
    try:
        hf = helpmenu.focus_get()
    except:
        hf = "x"

    try:
        top = root.attributes('-topmost')
        if top:
            printdbg("#4 return \n")
            return
    except:
        top = 0

    if hf == None:
        if unexpose_handler.inrun:
            printdbg("#5 return \n")
            return
        unexpose_handler.inrun = 1
        helpmenu.destroy()
        helpmenu = create_cascade_menu()
        menubar.entryconfigure(1, menu = helpmenu, state = NORMAL)
        unexpose_handler.inrun = 0
        printdbg("foucus out done")
    printdbg("")

unexpose_handler.inrun = 0
unexpose_handler.dbg = 0

helpmenu.bind_all("<FocusOut>", unexpose_handler)


def get_methods(object):
    return [method_name for method_name in dir(object) \
        if callable(getattr(object, method_name))]

def get_variables(object):
    return [method_name for method_name in dir(object) if not callable(getattr(object, method_name))] \
         + [getattr(object, variable_name) for variable_name in vars(object)]

################################################################################

def console_infostart_prints():
    global filename, dir_path, shellbin

    network_has_ipv6 = urllib3.util.connection.HAS_IPV6
    # This line can enable or disable the IPv6 for 'requests' methods
    urllib3.util.connection.HAS_IPV6 = True

    try:
        ipv6_system_check_thread.join()
    except:
        pass

    strn = environ.get('SHELL')
    if strn: shellbin = strn

    print(f"\nthis script {filename} for {gui_version_str} uses {shellbin}",
           "\nscript path", dir_path,
           "\nipaddr url4", ", ".join(get_ipaddr_info.wurl4),
           "\nipaddr url6", ", ".join(get_ipaddr_info.wurl6),
           "\nnetwork has", ("IPv6" if network_has_ipv6 else "IPv4"),
           ("enabled (1)" if urllib3.util.connection.HAS_IPV6 else "disabled (0)"),
            "while system IPv6 support is",
           ("enabled (1)" if ipv6_system_check.enabled else "disabled (0)"),
           "\n");

    try:
        acc_info_update_thread.join()
    except:
        pass

################################################################################

root.config(menu=menubar)
root.tr = UpdateThread()
root.update_idletasks()
root.mainloop()
kill_weather_xterm()
try: root.destroy()
except: pass

