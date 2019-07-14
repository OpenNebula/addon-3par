#!/bin/bash

# -------------------------------------------------------------------------- #
# Copyright 2019, FeldHost™ (feldhost.net)                                    #
#                                                                            #
# Portions copyright 2015-2018, Storpool (storpool.com)                      #
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
#--------------------------------------------------------------------------- #

set -e

PATH="/bin:/usr/bin:/sbin:/usr/sbin:$PATH"

CP_ARG=${CP_ARG:--uv}

ONE_USER=${ONE_USER:-oneadmin}
ONE_VAR=${ONE_VAR:-/var/lib/one}
ONE_LIB=${ONE_LIB:-/usr/lib/one}
ONE_DS=${ONE_DS:-/var/lib/one/datastores}

if [ -n "$ONE_LOCATION" ]; then
    ONE_VAR="$ONE_LOCATION/var"
    ONE_LIB="$ONE_LOCATION/lib"
    ONE_DS="$ONE_LOCATION/var/datastores"
fi


#----------------------------------------------------------------------------#

[ "${0/\//}" != "$0" ] && cd ${0%/*}

CWD=$(pwd)

function findFile()
{
    local c f d="$1" csum="$2"
    while read c f; do
        if [ "$c" = "$csum" ]; then
            echo $f
            break
        fi
    done < <(md5sum $d/* 2>/dev/null)
}

function tmResetMigrate()
{
    local current_csum=$(md5sum "${M_DIR}/${MIGRATE}" | awk '{print $1}')
    local csum comment found orig_csum
    while read csum comment; do
        [ "$comment" = "orig" ] && orig_csum="$csum"
        if [ "$current_csum" = "$csum" ]; then
            found="$comment"
            break;
        fi
    done < <(cat "tm/${TM_MAD}-${MIGRATE}.md5sums")
    case "$found" in
         orig)
            ;;
         4.10)
            true
            ;&
         4.14)
            orig=$(findFile "$M_DIR" "$orig_csum" )
            if [ -n "$orig" ]; then
                echo "***   $found variant of $TM_MAD/$MIGRATE"
                mv "${M_DIR}/${MIGRATE}" "${M_DIR}/${MIGRATE}.backup$(date +%s)"
                echo "***   restoring from original ${orig##*/}"
                cp $CP_ARG "$orig" "${M_DIR}/${MIGRATE}"
            fi
            ;;
         5.00)
            continue
            ;;
            *)
            echo " ** Can't determine the variant of $TM_MAD/$MIGRATE"
    esac
}

if [ -f "$ONE_VAR/remotes/VERSION" ]; then
    [ -n "$ONE_VER" ] || ONE_VER="$(< "$ONE_VAR/remotes/VERSION")"
    ONE_VER=$(echo $ONE_VER| cut -d '.' -f 1,2,3)
fi
OIFS=$IFS
IFS='.'
IFS=$OIFS

if [ -f "scripts/install-${ONE_VER}.sh" ]; then
    source "scripts/install-${ONE_VER}.sh"
else
    echo "ERROR: Unknown OpenNebula version '$ONE_VER' detected!"
    echo "Please install manually"
    echo
    exit 1
fi