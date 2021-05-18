# coding=utf-8

import urllib
import base64
import urlparse
import json
import hashlib

GFWLIST_HOSTS = (
    "https://bitbucket.org/gfwlist/gfwlist/raw/HEAD/gfwlist.txt",
    "https://pagure.io/gfwlist/raw/master/f/gfwlist.txt",
    "https://repo.or.cz/gfwlist.git/blob_plain/HEAD:/gfwlist.txt",
    "https://gitlab.com/gfwlist/gfwlist/raw/master/gfwlist.txt",
    "https://git.tuxfamily.org/gfwlist/gfwlist.git/plain/gfwlist.txt",
    "https://raw.githubusercontent.com/gfwlist/gfwlist/master/gfwlist.txt",
)

PAC_TMPL = """//generated from gfwlist

var proxy = "SOCKS5 127.0.0.1:__PROXY_PORT__; SOCKS 127.0.0.1:__PROXY_PORT__; DIRECT;";

var domains = __DOMAINS__;

var direct = 'DIRECT;';

var hasOwnProperty = Object.hasOwnProperty;

function FindProxyForURL(url, host) {
    var suffix;
    var pos = host.lastIndexOf('.');
    pos = host.lastIndexOf('.', pos - 1);
    while(1) {
        if (pos <= 0) {
            if (hasOwnProperty.call(domains, host)) {
                return proxy;
            } else {
                return direct;
            }
        }
        suffix = host.substring(pos + 1);
        if (hasOwnProperty.call(domains, suffix)) {
            return proxy;
        }
        pos = host.lastIndexOf('.', pos - 1);
    }
}
"""

def get_gfwlist_file(save_to):
    """
    download gfwlist raw data
    """
    res = None
    for url in GFWLIST_HOSTS:
        try:
            res = urllib.urlopen(url)
        except IOError:
            continue
        break

    print "get content from: %s" % res.geturl()
    print "http response status: %s" % res.getcode()
    res_data = res.read()

    with open(save_to, "wb") as f:
        f.write(res_data)


def update_gfwlist(target_file, proxy_port):
    """
    update gfwlist rules
    """
    download_file = "./pac/gfwlist.txt"
    get_gfwlist_file(download_file)
    try:
        last_md5 = None
        last_md5 = open(download_file + ".md5").read().strip()
    except Exception as e:
        print e
        pass
    new_md5 = hashlib.md5(open(download_file).read()).hexdigest()

    if new_md5 == last_md5:
        return False

    pac_content = genpac(download_file, proxy_port)
    with open(target_file, "wb") as f:
        f.write(pac_content)
    
    with open(download_file + ".md5", "wb") as f:
        f.write(new_md5)
    
    return True


def genpac(gfwlist_file, proxy_port):
    """
    gen pac file from gfwlist
    """
    with open(gfwlist_file) as f:
        data = f.read()
    rules_content = base64.b64decode(data)

    domains_dict = {}
    for line in rules_content.splitlines():
        # line to ignore
        line = urllib.unquote(line)
        if line.startswith("!"):
            continue
        if line.startswith("["):
            continue
        if line.startswith("@"):
            continue
        if line.find(".*") >= 0:
            continue

        # line to strip
        if line.startswith("||"):
            line = line.lstrip("||")
        if line.startswith("|"):
            line = line.lstrip("|")
        if line.startswith("."):
            line = line.lstrip(".")
        
        # line startswith http:// or https://
        if line.startswith("https://") or line.startswith("http://"):
            line = urlparse.urlparse(line).netloc
        
        if line.find("/") >= 0:
            line = line.split("/")[0]
        
        if line == "":
            continue
        if line.find("*") >= 0:
            continue
        if line.find(".") < 0:
            continue
        
        domains_dict[line] = 1

    pac_content = PAC_TMPL.replace("__PROXY_PORT__", proxy_port)
    pac_content = pac_content.replace("__DOMAINS__", json.dumps(domains_dict, indent=2))

    return pac_content


if __name__ == "__main__":
    pass