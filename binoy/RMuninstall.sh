#!/bin/sh

# $Header: RM/RLuninst 1.00 17/04/2000 RM Copyright (c) 2000-2016, Hitachi, Ltd.
# $Header: RM/RLuninst 1.00 17/04/2000 RM (C) Copyright 2000-2016 Hewlett Packard Enterprise Development LP.
#
# NAME  : Raid Manager and Raid Manager/LIB UNinstallation SHELL.
#
# DESCRIPTION:
# RM/RLuninst is script that can be executing automatically an uninstallation
# procedure which is describing into RMreadme and RLreadme.
# This script is copied to 'Specified directory/$RMDIR' under through 
# the installation 
# of the RM/RLinstsh.
# Also this script can be accomplishing automatically an uninstallation 
# by executing and deleting myself.
# When you have to uninstall of the Raid Manager,
# please executes RM/RLuninst which was copied to 'Specified directory/$RMDIR'
# under or placed RM/RLuninst on the CD. 
#
# CHANGELOG
#
# Revision 1.08   03/23/2016   i.uratani
#                 Added to back-up horcm.pem.
#
# Revision 1.07   07/11/2001   k.urabe
#                 Changed pnkill() due to killed myself.
#
# Revision 1.06   27/06/2001   k.urabe
#                 Added pnkill() for HP-UX.
#
# Revision 1.05   20/09/2000   k.urabe
#                 Added UNIX_SV for HORCM.
# 
# Revision 1.04   03/08/2000   k.urabe
#                 Added IRIX64 for HORCM.
# 
# Revision 1.03   24/07/2000   k.urabe
#                 Added MPE/iX for HORCM and RMLIB.
#                 Changed option of '/bin/rm' to '/bin/rm -rf ...' for MPE/iX.
#
# Revision 1.02   27/05/2000   k.urabe
#                 Deleted $RMOBJ & $XPOBJ due to a file name's differing from
#                 a hard disk on the Multiplathome for CD(ISO2 or RockRidg etc).
#
# Revision 1.01   27/04/2000   k.urabe Fixed revision
#                 Added $RMROOT for checking of specified directory.
# 
# Revision 1.00   24/04/2000   k.urabe Initial revision




# [STARTING POINT]:

# In case of RMuninst, you have to define $execname as "RM" 
# and also changes file name as RMuninst. 
 execname="RM"

# In case of RLuninst, you have to define $execname as "RL"
# and also changes file name as RLuninst.
#execname="RL"


# $RMROOT  Root Path for $RMDIR.
# $RMPTH   Path for Symbolical link or directory. 
#          This variable(/HORCM) must not be changed.
# $RMDIR   Directory which is made by cpio command.
#          This variable(HORCM) must not be changed.
# $UNLINKSH  UNlink shell name of the Raid Manager 
# $uninsh  UNInstallation shell name that execute $excnm as itself.
# $excnm   UNInstallation shell name.

osname=`uname`

if [ "$execname" = "RM" ]
  then
    RMROOT="/"
    RMDIR="HORCM"
    RMPTH="${RMROOT}$RMDIR"
    MGRNM="HORCM"
    UNLINKSH="horcmuninstall.sh"
    LINKSH="horcminstall.sh"
    uninsh="RMuninst"
    instsh="RMinstsh"
    excnm="RMuninstall.sh"
    if [ "$osname" != "MPE/iX" ]
      then
        OLDOBJ="RMOLD.cpio"
      else
        OLDOBJ="RMOLD.tar"
    fi
    ISRMLIB=0
  else
    RMROOT="/usr/lib"
    RMDIR="RMLIB"
    RMPTH="${RMROOT}/$RMDIR"
    MGRNM="Manager"
    UNLINKSH="rmlibuninstall.sh"
    LINKSH="rmlibinstall.sh"
    uninsh="RLuninst"
    instsh="RLinstsh"
    excnm="RLuninstall.sh"
    if [ "$osname" != "MPE/iX" ]
      then
        OLDOBJ="RMLIBOLD.cpio"
      else
        OLDOBJ="RMLIBOLD.tar"
    fi
    ISRMLIB=1
fi



# These functions are used as instead of the 'awk' and 'set'
# that may not be able to use on the Multiple Plat.

getn(){
  _argc=0
  _rval=0
  for _data in $*
  do
    _argc=`expr $_argc + 1`
    if [ $_argc -ne 1 ]
      then
        if [ $_argc -eq $_p1 ]
        then
          E1=$_data
          _rval=`expr $_argc - 1`
        fi
      else
        _p1=`expr $1 + 1`
    fi
  done
  return $_rval ;
}


#Example for getn():
#tdata="12 23 56 78"
#read tdata
#getn 1 $tdata
#echo $? $E1
#exit


getfnx1(){
  _argc=0
  _fargc=0
  _rval=0
  for _data in $*
  do
    _argc=`expr $_argc + 1`
    if [ $_argc -ne 1 ]
      then
        if [ $_fargc -eq 0 -a "$_data" = "$1" ]
          then
            _fargc=`expr $_argc + 1`
        fi
        if [ $_fargc -eq $_argc ]
          then
            E1=$_data
            _rval=`expr $_fargc - 1`
        fi
    fi
  done
  return $_rval ;
}



#Example for getfnx1():
#instdir=`ls -l /HORCM`
#instdir="lrwxrwxrwx   1 root  system   10 Apr 20 16:14 /HORCM -> /tmp/HORCM"
#getfnx1 "->" $instdir
#echo $? $E1
#exit


getrmver(){
  if [ $ISRMLIB -ne 1 ]
    then
      ver=`raidqry -h`
      status=$?
    else
      ver=`${1}/bin/whatrmver`
      if [ "$ver" = ""  ]
        then
          status=1
        else
          status=0
      fi
  fi
  return $status ;
  
}



pnkill(){
  _pname=$1
  _pwait=0
  _pfind=1
  _psin=`/bin/ps -e | grep $_pname`

  while [ $_pfind -ne 0 -a "$_psin" != "" ]
  do
    _pfind=0
    set $_psin
    while [ $# -ge 4 ]
    do
      if [ "$4" = "$_pname" ]
        then
          _pfind=1
          if [ $_pwait -eq 0 ]
            then
              /bin/kill -9 $1
            else
              echo "Waiting to terminate $4 [PID = $1]."
          fi
      fi
      shift
    done
    if [ $_pfind -ne 0 ]
      then
        _pwait=1
        sleep 3
        _psin=`/bin/ps -e | grep $_pname`
    fi
  done ;
}


umask 0
curdir=`pwd`


if [ "$0" != "/tmp/${excnm}" -a "$0" != "./${excnm}" -a "$0" != "$excnm" ]
  then
    if [ -f ${RMPTH}/$uninsh ]
      then
# Executes its myself as RM/RLuninstall.sh 
        /bin/cp ${RMPTH}/$uninsh /tmp/${excnm}
        /bin/chmod 544 /tmp/${excnm}
        exec /tmp/${excnm} 
# NOT reached
        echo "Execution for $excnm was failed." 
        exit 1      
    fi
fi

# I am a RM/RLuninstall.sh

if [ -d $RMPTH -o -h $RMPTH ]
  then
    if [ -h $RMPTH ]
      then
        instdir=`/bin/ls -l $RMPTH`
        getfnx1 "->" $instdir
        cd $E1
      else
        cd $RMPTH        
    fi
    cd ..
    curinstdir=`pwd`

    if [ "$curinstdir" = "/" ]
      then
        instrmdir="/$RMDIR"
        curobjfile="/$OLDOBJ"
      else
        instrmdir="${curinstdir}/$RMDIR"
        curobjfile="${curinstdir}/$OLDOBJ"
    fi

# 160323
    if ls /HORCM/usr/auth/* >/dev/null 2>&1
      then
        /bin/cp /HORCM/usr/auth/* /tmp/
    fi
# 160323

    echo "******************* Confirmation for deletion of the ${RMDIR}.**********************"
    echo "Please confirms whether $MGRNM has performing or not."
    if [ $ISRMLIB -ne 1 ]
      then
        echo "If $MGRNM has performing then stop by using horcmshutdown.sh and please try again."
        echo "- In case of 1 instance configuration of HORCM"
        echo "  # horcmshutdown.sh"
        echo "- In case of multiple instances configuration of HORCM"
        echo "  # horcmshutdown.sh  0 1 ..."
        echo "Also If HORC commands has performing in the interactive mode"
        echo "then terminates these commands by using -q option."
      else
        echo "If $MGRNM has performing then stop the Manager and please try again."
    fi

    mvmd=0    
    go=1
    while [ $go -ne 0 ]
    do
      echo "For delete  -> please enter 'return key' for deletes $RMDIR of '${curinstdir}' under."
      echo "For cancel  -> please enter 'exit'." 
      echo "For delete & change to preserved $RMDIR -> please enter a 'directory' where $RMDIR is preserved."
      read arg
      getn 1 $arg 
      if [ $? -ne 0 ]
        then
          if [ "$E1" = "exit" ]
            then
              exit 1
            else
              if [ -d $E1 ] 
                then
                  cd $E1
                  mvinstdir=`pwd`
                  if [ "$mvinstdir" = "/" ]
                    then
                      mvinstrmdir="/$RMDIR"
                      mvobjfile="/$OLDOBJ"
                    else
                      mvinstrmdir="${mvinstdir}/$RMDIR"
                      mvobjfile="${mvinstdir}/$OLDOBJ"
                  fi
                  if [ -d $mvinstrmdir ] 
                    then
                      if [ "$mvinstdir" != "$curinstdir" -a "$mvinstdir" != "$RMROOT" ]
                        then
                          mvmd=1
                          go=0
                        else
                          echo "A specified directory '${E1}' is already installing directory as '${RMDIR}'."
                      fi
                    else
                      echo "'${RMDIR}' directory does not existing to '${E1}' under."
                  fi
                else
                  echo "A specified directory '${E1}' does not existing as a directory."
              fi
          fi
        else
         go=0
      fi    
    done

    if [ "$osname" = "HP-UX" -a $ISRMLIB -ne 1 ]
      then
        pnkill "inqraid"
    fi

# Executes saving of $instrmdir under.

    if  [ $mvmd -eq 1 ]
      then
        cd $curinstdir
        osname=`uname`
        getrmver $mvinstrmdir
        if [ $? -ne 0 ]
          then 
            echo "This uninstallation was canceled due to failed on the getrmver."
            exit 1
        fi
        set $ver
# I do not be saving $instsh to cpio file.
        if [ -f ./${RMDIR}/$instsh ]
          then
            /bin/rm -rf ./${RMDIR}/$instsh 
        fi
# I do not be saving $uninsh to cpio file.
        if [ -f ./${RMDIR}/$uninsh ]
          then
            /bin/rm -rf ./${RMDIR}/$uninsh 
        fi
        if [ "$osname" = "MPE/iX" ]
          then
            /bin/tar cf $mvobjfile $RMDIR 2>/dev/null 
          elif [ "$osname" = "Linux" -o "$osname" = "IRIX64" ]
          then
            /usr/bin/find $RMDIR -print | /bin/cpio -o > $mvobjfile 2>/dev/null
          elif [ "$osname" = "UNIX_SV" ]
          then
            /usr/bin/find $RMDIR -print | /bin/cpio -oc > $mvobjfile 2>/dev/null
          else
            /bin/find $RMDIR -print | /bin/cpio -odmu > $mvobjfile 2>/dev/null
        fi
        if [ ! -f $mvobjfile ]
          then
            echo "This uninstallation was canceled due to failed on the saving state."
            exit 1
        fi
        /bin/chmod 544 $mvobjfile 
        if [ $ISRMLIB -ne 1 ]
          then
            echo "${RMDIR}(${4}${5}) of '${curinstdir}' was saved as '${mvobjfile}'."
          else
            echo "${RMDIR}(${3}) of '${curinstdir}' was saved as '${mvobjfile}'."
        fi
    fi

# Executes deletion of $instrmdir from here.

    symlink=1
    cd /
#   if  [ $mvmd -ne 1 -o $ISRMLIB -eq 1 ]
    if  [ $mvmd -ne 1  ]
      then
        ${RMPTH}/$UNLINKSH > /dev/null
    fi
    if [ -h $RMPTH ]
      then
        /bin/rm  $RMPTH 
        symlink=$?      
    fi
    echo "rm -rf $instrmdir"
    /bin/rm -rf $instrmdir

    if [ -d $instrmdir -o $? -ne 0 ]
      then
        if [ $symlink -eq 0 ]
          then
            /bin/ln -s $instrmdir  $RMPTH
        fi
        echo "Please confirms whether $MGRNM has performing or not."
        if [ $ISRMLIB -ne 1 ]
          then
            echo "If $MGRNM has performing then stop by using horcmshutdown.sh and please try again."
          else
            echo "If $MGRNM has performing then stop the Manager and please try again."
        fi
        exit 1
    fi

    if [ -f $curobjfile ]
      then
        /bin/rm -rf $curobjfile > /dev/null
    fi
    
    if  [ $mvmd -ne 1 ]
      then
        echo "This uninstallation was successful."
        exit 0
    fi

# Executes changing of $mvinstrmdir from here. 
  
    if [ "$mvinstrmdir" != "$RMPTH" ]
      then
        /bin/ln -s $mvinstrmdir  $RMPTH
    fi

    cd $mvinstrmdir

    ${mvinstrmdir}/$LINKSH > /dev/null

    getrmver $mvinstrmdir

    if [ $? -ne 0 ]
      then 
        echo "This uninstallation for changing was failed."
        exit 1
    fi

    set $ver
    echo "'${RMPTH}' was changed to the following version as '${mvinstrmdir}'."

    if [ $ISRMLIB -ne 1 ]
      then
        echo "[ $1 $2 $3 $4 $5 ]"
      else
        echo "[ $1 $2 $3 for $RMDIR ]"
    fi
    echo "--------------------------------------------------------------------------------"
    /bin/ls $mvinstrmdir
    echo "--------------------------------------------------------------------------------"
  else
    if [ $ISRMLIB -ne 1 ]
      then 
        echo "$RMDIR is not installed for this machine."
      else
        echo "$RMDIR is not installed for this machine."
    fi
    exit 1   
fi
exit 0




