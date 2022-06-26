Vagrant.configure("2") do |config|

  config.vm.define "freebsd" do |machine|
    machine.vm.box = "generic/freebsd13"
    setup_rsync(machine)
    machine.vm.provision "shell", privileged: false, inline:<<-END
      sudo pkg update
      sudo pkg install -y fish py38-pip py38-sqlite3
      cd /io && pip install -e .[test] psutil
    END
    setup_shell(machine)
  end

  config.vm.define "openbsd" do |machine|
    machine.vm.box = "generic/openbsd7"
    setup_rsync(machine)
    machine.vm.provision "shell", privileged: false, inline:<<-END
      sudo pkg_add fish py3-pip
      cd /io && pip install -e .[test] psutil
    END
    setup_shell(machine)
  end

  config.vm.define "netbsd" do |machine|
    machine.vm.box = "generic/netbsd9"
    setup_rsync(machine)
    machine.vm.provision "shell", privileged: false, inline:<<-END
      echo y | sudo pkgin install fish py39-pip py39-sqlite3
      cd /io && pip3.9 install -e .[test] psutil
    END
    setup_shell(machine)
  end

#   config.vm.define "dragonflybsd" do |machine|
#     machine.vm.box = "generic/dragonflybsd5"
#     machine.vm.provision "shell", inline:<<-END
#       sudo sh -c 'echo PKG_ENV { SSL_NO_VERIFY_PEER=1 } >> \
#         /usr/local/etc/pkg.conf'
#     END
#     setup_rsync(machine)
#     machine.vm.provision "shell", privileged: false, inline:<<-END
#       echo y | sudo pkg install fish
#       echo y | sudo pkg install py37-pip py37-sqlite3
#       cd /io
#       pip install -e .[test] psutil
#     END
#     setup_shell(machine)
#   end
#
#   config.vm.define "hardenedbsd" do |machine|
#     machine.vm.box = "generic/hardenedbsd13"
#     setup_rsync(machine)
#     machine.vm.provision "shell", privileged: false, inline:<<-END
#       sudo pkg update
#       sudo pkg install -y fish
#       sudo pkg install -y py38-pip py38-sqlite3
#       cd /io
#       pip install -e .[test] psutil
#     END
#     setup_shell(machine)
#   end

end

def setup_rsync(machine)
  ignored = `git ls-files --exclude-standard -oi --directory`
  machine.vm.synced_folder ".", "/io", type: "rsync",
    rsync__exclude: ignored.split()
end

def setup_shell(machine)
  machine.vm.provision "shell", privileged: false, inline:<<-END
    sudo chsh -s $(which fish) $USER
    echo '' | fish --login
    echo 'cd /io' >> ~/.config/fish/config.fish
    echo set PATH ~/.local/bin '$PATH' >> ~/.config/fish/config.fish
  END
end
