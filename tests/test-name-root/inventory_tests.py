#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Tests to compare the ini and yaml based inventorys.
#
# This script was written by Stefan Berggren <nsg@nsg.cc>
# This code is released under the MIT license.
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
import os
import unittest
import operator

from ansible import errors
from ansible.inventory import Inventory

from ansible import __version__ as ansible_version

if ansible_version[0]!="1":
    from ansible.parsing.dataloader import DataLoader
    from ansible.vars import VariableManager

class AnsibleInventoryTests(unittest.TestCase):
    if ansible_version[0]=="1":
        yml_inv = Inventory("{}/inv.sh".format(os.path.dirname(__file__)))
    else:
        var_manager = VariableManager()
        dataloader = DataLoader()
        yml_inv = Inventory(host_list="{}/inv.sh".format(os.path.dirname(__file__)),loader=dataloader,variable_manager=var_manager)

    def test_check_group_vars_host1(self):
        if ansible_version[0]=="1":
            yml = self.yml_inv.get_variables("myhost1.example.com")
        else:
            yml = self.yml_inv.get_vars("myhost1.example.com")
        result = {
            'inventory_hostname': u'myhost1.example.com',
            'group_names': [
                u'com',
                u'example',
                u'foo',
                u'foo-docker',
                u'foo-docker-com',
                u'foo-docker-example',
                u'foo-docker-myhost',
                u'myhost'
                ],
            'inventory_hostname_short': u'myhost1'
            }
        self.assertDictEqual(yml, result, msg="\nGot:    {}\nExpect: {}".format(yml, result))

if __name__ == '__main__':
    print("\n### Execute test {}\n".format( __file__))
    unittest.main(verbosity=2)