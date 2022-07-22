Vagrant.configure("2") do |config|

  config.vm.define "freebsd" do |machine|
    machine.vm.box = "generic/freebsd13"
    setup_rsync(machine)
    machine.vm.provision "shell", privileged: false, inline:<<-END
      sudo pkg update
      sudo pkg install -y fish py39-pip py39-sqlite3
      cd /io && pip install -e .[test] psutil
    END
    setup_shell(machine)
    shimify_python(machine, "python3.9")
  end

  config.vm.define "openbsd" do |machine|
    machine.vm.box = "generic/openbsd7"
    setup_rsync(machine)
    machine.vm.provision "shell", privileged: false, inline:<<-END
      sudo pkg_add fish py3-pip
      cd /io && pip install -e .[test]
    END
    setup_shell(machine)
    shimify_python(machine, "python3")
  end

  config.vm.define "netbsd" do |machine|
    machine.vm.box = "generic/netbsd9"
    setup_rsync(machine)
    machine.vm.provision "shell", privileged: false, inline:<<-END
      echo y | sudo pkgin install fish py39-pip py39-sqlite3
    END
    setup_shell(machine)
    shimify_python(machine, "python3.9")
    machine.vm.provision "shell", privileged: false, inline:<<-END
      cd /io && pip install -e .[test] psutil
    END
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
    echo set -x FORCE_COLOR 1 >> ~/.config/fish/config.fish
  END
end

def shimify_python(machine, python)
  commands = <<-END
    #!/usr/bin/env fish
    echo -e '#!/usr/bin/env fish\\n%s $argv' > /usr/bin/python
    echo -e '#!/usr/bin/env fish\\n%s -m pip $argv' > /usr/bin/pip
    chmod +x /usr/bin/python /usr/bin/pip
  END
  commands = commands % [python, python]
  machine.vm.provision "shell", privileged: true, inline: commands
end
