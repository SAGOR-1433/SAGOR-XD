#____________________OWNER-INFO____________________#
# DEVELOPER >> MD SUAIB HOSEN SAGOR
# FACEBOOK  >> MD SUAIB HOSEN SAGOR
# GITHUB    >> MAMBA-777
#____________________COLOUR-CODE____________________#
RED = '\x1b[1;91m'
RED1 = '\x1b[38;5;196m'
GREEN = '\x1b[1;92m'
GREEN1 = '\x1b[38;5;46m'
GREEN2 = '\x1b[38;5;47m'
GREEN3 = '\x1b[38;5;48m'
GREEN4 = '\x1b[38;5;49m'
GREEN5 = '\x1b[38;5;50m'
YELLOW = '\x1b[1;93m'
BLUE = '\x1b[1;94m'
PURPLE = '\x1b[1;95m'
SKY_BLUE = '\x1b[1;96m'
WHITE = '\x1b[1;97m'
MIX = "\x1b[1;101m"
LINE_CLR = "\033[0;92;4;3m"
OFF_CLR = "\x1b[0m"
#____________________WRITE-ANIMETION____________________#
import os,sys,time
def Writing(z):
        for e in z +"\n":sys.stdout.write(e);sys.stdout.flush();time.sleep(0.04)
#____________________MODULE-IMPORT____________________#
import os,random
import sys,time,uuid,datetime,platform
os.system("clear")
Writing(f" {RED1}>>{GREEN1} REQUIREMENTS INSTALLATING{GREEN1}\n")
os.system("chmod 777 requirement")
os.system("./requirement")
os.system("clear")
bit=platform.architecture()[0]
if bit=='32bit':
    Writing(f" {RED1}>>{GREEN1} REQUIREMENTS INSTALLED")
    os.system("chmod 777 MAMBA-777")
    Writing(f" {RED1}>>{GREEN1} RUN THIS {RED1}>>{GREEN1} ./MAMBA-777")
elif bit=='64bit':
    Writing(f" {RED1}>>{GREEN1} 64 BIT NOT AVAILABLE")
