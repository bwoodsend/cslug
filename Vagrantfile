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
