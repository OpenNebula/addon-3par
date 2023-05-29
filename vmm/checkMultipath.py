# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------- #
# Copyright 2022, FeldHost™ (feldhost.net)                                   #
#                                                                            #
# Licensed under the Apache License, Version 2.0 (the "License"); you may    #
# not use this file except in compliance with the License. You may obtain    #
# a copy of the License at                                                   #
#                                                                            #
# http://www.apache.org/licenses/LICENSE-2.0                                 #
#                                                                            #
# Unless required by applicable law or agreed to in writing, software        #
# distributed under the License is distributed on an "AS IS" BASIS,          #
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.   #
# See the License for the specific language governing permissions and        #
# limitations under the License.                                             #
# -------------------------------------------------------------------------- #

import sys
import dmmp

wwid = sys.argv[1]

mpath = dmmp.mpath_get(wwid)
print("Got mpath: wwid '%s', name '%s'" % (mpath.wwid, mpath.name))
for pg in mpath.path_groups:
    print("\tGot path group: id '%d', priority '%d', status '%d(%s)', "
          "selector '%s'" %
          (pg.id, pg.priority, pg.status, pg.status_string, pg.selector))

    target = None
    for p in pg.paths:
        # check for target wwn, must be same for all paths
        if target is not None and target != p.target_wwnn:
            print("\t\tPath: blk_name '%s', status '%d(%s)' has different target wwnn '%s'!" %
                  (p.blk_name, p.status, p.status_string, p.target_wwnn))
            exit(1)
        else:
            target = p.target_wwnn
            print("\t\tGot path: blk_name '%s', status '%d(%s)', target '%s'" %
                  (p.blk_name, p.status, p.status_string, p.target_wwnn))
