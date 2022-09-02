import os, sys, subprocess

args = sys.argv

if __name__ == '__main__':
  if args[1] == 'start':
    subprocess.run('uvicorn main:app --reload', shell=True)
  elif args[1] == 'install':
    subprocess.run('pip install -r reqirements.txt')
  elif args[1] == 'freeze':
    output = subprocess.run('pip freeze > reqirements.txt',shell=True)
