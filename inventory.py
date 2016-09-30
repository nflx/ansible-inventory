#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Define your Ansible inventory in structured YAML. Ansible is basically YAML
# and python anyway. I never understood why they choose to introduce INI as
# an inventory format.
#
# This script was written by Stefan Berggren <nsg@nsg.cc> from inspiration
# from Anton Lindström and Tim Rice. This code is released under the MIT
# license.
#
# Repo: https://github.com/nsg/ansible-inventory
# Wiki: https://github.com/nsg/ansible-inventory/wiki
#
# The MIT License (MIT)
# 
# Copyright (c) 2015 Stefan Berggren
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from __future__ import print_function
from pprint import pprint,pformat
import yaml
import json
import sys
import re
import os
import argparse

_data = { "_meta" : { "hostvars": {} }}
_matcher = {}
_hostlog = []

# Nice output
def print_json(data):
    print(json.dumps(data, indent=2))

# Load the YAML file
def load_file(file_name):
    with open(file_name, 'r') as fh:
        return yaml.load(fh)

def get_yaml(file_name):
    script_path = os.path.dirname(os.path.realpath(__file__))
    file_name = file_name.replace(script_path, '')
    return load_file("{}/{}".format(script_path, file_name))

def to_num_if(n):
    try:
        return int(n)
    except:
        pass
    try:
        return float(n)
    except:
        return n

class Host:

    def __init__(self, host, path):
        self.path = path
        self.var = {}
        self.name = ""
        self.path = ""
        self.tags = []

        if type(host) == dict:
            for k in host:
                if k == 'name':
                    self.name = host['name']
                elif k == 'tags':
                    for tag in host[k]:
                        self.tags.append(tag)
                else:
                    self.var[k] = host[k]
        elif type(host) == str:
            self.name = host

        if self.name in _hostlog:
            raise Exception("Error, host {} defined twice".format(self.name))
        _hostlog.append(self.name)

        self.tags = self.tags + self.split_tag() + self.matcher_tags()

        if len(self.var) > 0:
            _data['_meta']['hostvars'][self.name] = self.var
        for tag in self.tags:
            if not tag in _data:
                _data[tag] = { "hosts": [] }
            if not 'hosts' in _data[tag]:
                _data[tag]['hosts'] = []
            _data[tag]['hosts'].append(self.name)


    def split_tag(self):
        tags = []
        for part in re.compile('[^a-z]').split(self.name):
            if part == "": continue
            tags.append(part)
        return tags

    def matcher_tags(self):
        tag = []
        for match in _matcher:
            m = re.compile(match['regexp']).match(self.name)
            if m:
                if 'groups' in match:
                    for g in match['groups']:
                        tag.append(g)
                if 'capture' in match and match['capture']:
                    for m2 in m.groups():
                        tag.append(m2)
        return tag

    def group(self):
        return "-".join(self.path)

    def __repr__(self):
        return "host: {} group: {} vars: {} tags: {}".format(
                self.name, self.group(), self.var, self.tags)

class Groups:
    def __init__(self, groups, path=["root"], hardlimit=None):

        if hardlimit:
            if type(hardlimit) != list:
               hardlimit=[hardlimit]
            print("groups: %s  hardlimit: %s\n\n" % (pformat(groups),pformat(hardlimit)))
        # Call a subgroup (or vars)
        godeeper=True
        if type(groups) == dict:
            fullmatched=False
            partmatched=False
            for g in groups:
                pd=len(path) # pd=pathdepth. (root/=0) docker=1  docker/site_a=2 ...
                pathstr='/'.join(path[1:]+[g])
                print("current group %s\n" % g)
                print("current path %s\n" % pathstr)
                print("current pd %s\n" % pd)
                if hardlimit:
                    for limit in hardlimit:
                        print("current limit %s" % limit)
                        nsd=len(limit.strip('/').split('/'))
                        print("nsd %s" % nsd)
                        if nsd == pd:
                            print("matching against pathstr %s " % (pathstr))
                            if re.compile(limit).match(pathstr):
                                fullmatched=True
                                print("*full match*")
                            else:
                                #if not fullmatched: fullmatched=False
                                print("_no full match_")
                        elif pd > nsd:
                            #if partmatched:
                            fullmatched=True
                        elif pd < nsd:
                            print("matching against ns pathstr %s " % (pathstr))
                            nspathstr='/'.join(path[1:]+[g])
                            if re.compile('/'.join(limit.strip('/').split('/')[:pd])).match(pathstr):
                                partmatched=True
                                print("*part match*")
                            else:
                                if (not fullmatched and not partmatched):
                                    partmatched=False
                                    print("_no part match_")
                    if g == 'hosts':
                        if fullmatched:
                            godeeper=True
                        else:
                            godeeper=False

                #
                # proceed deeper if no limit was hit
                if godeeper:
                    p = path + [g]
                    fullpath = "-".join(p)
                    if 'vars' == p[-1]:
                        _data["-".join(path)]['vars'] = groups['vars']
                    elif 'include' in p[-1]:
                        for f in groups['include']:
                            Groups(get_yaml(f), p[:len(p)-1], hardlimit=hardlimit)
                    else:
                        if 'hosts' != p[-1]:
                            if partmatched or fullmatched:
                                if not fullpath in _data:
                                    _data[fullpath] = {}
                                if not 'children' in _data["-".join(path)]:
                                    _data["-".join(path)]['children'] = []

                                    # workaround for https://github.com/ansible/ansible/issues/13655
                                    if not 'vars' in _data["-".join(path)]:
                                        _data["-".join(path)]['vars'] = {}

                                _data["-".join(path)]['children'].append("-".join(p))
                        if partmatched or fullmatched:
                            Groups(groups[g], p, hardlimit=hardlimit)

        # Process groups
        elif type(groups) == list:
            for h in groups:
                if 'hosts' == path[-1]:
                    path.pop()
                hst = Host(h, path)
                fullpath = "-".join(path)
                for t in hst.tags:
                    tagfullpath = "{}-{}".format(fullpath,t)

                    if not tagfullpath in _data:
                        _data[tagfullpath] = {}
                    if not 'hosts' in _data[tagfullpath]:
                        _data[tagfullpath]['hosts'] = []

                    _data[tagfullpath]['hosts'].append(hst.name)

                    if not 'children' in _data[fullpath]:
                        _data[fullpath]['children'] = []

                        # workaround for https://github.com/ansible/ansible/issues/13655
                        if not 'vars' in _data[fullpath]:
                            _data[fullpath]['vars'] = {}

                    _data[fullpath]['children'].append(tagfullpath)

class TagVars:
    def __init__(self, tag, val):
        for k, v in val.items():
            if not tag in _data:
                _data[tag] = {}
            if not 'vars' in _data[tag]:
                _data[tag]['vars'] = {}
            _data[tag]['vars'][k] = v

class Inventory:
    commands = ["include", "matcher", "tagvars"]

    def __init__(self, ifile, hardlimit=None):
        json_data = get_yaml(ifile)
        global _matcher

        if 'matcher' in json_data:
            _matcher = json_data['matcher']

        if 'tagvars' in json_data:
            for tag,val in json_data['tagvars'].items():
                TagVars(tag, val)

        for el in json_data:
            if not el in self.commands:
                _data[el] = {}
                Groups(json_data[el], [el],hardlimit=hardlimit)
                break

def main(argv):
    global _meta

    parser = argparse.ArgumentParser(description='Ansible Inventory System')
    parser.add_argument('--list', help='List all inventory groups', action="store_true")
    parser.add_argument('--host', help='List vars for a host')
    parser.add_argument('--hardlimit', help='Limit sections of inventory to return. This is mostly to reduce performance hits in ansible >=2.x when running a large inventory.',action='append')
    parser.add_argument('--file', help='File to open, default inventory.yml', 
            default='inventory.yml')
    args = parser.parse_args()

    hardlimit = None
    if args.hardlimit:
        hardlimit=args.hardlimit
    inventory = Inventory(args.file,hardlimit)

    if args.list:
        print_json(_data)
    if args.host:
        if args.host in _data['_meta']['hostvars']:
            print_json(_data['_meta']['hostvars'][args.host])
        else:
            print_json({})

if __name__ == '__main__':
    sys.exit(main(sys.argv))
