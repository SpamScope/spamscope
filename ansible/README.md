# Overview
The Ansible playbook in this repository can help you to install Apache Storm and SpamScope on Debian servers. The ansible folder is complete with [ansible.cfg](./ansible.cfg) file.
You can use these playbooks with your Ansible infrastructure or from this folder.
Explain how Ansible works is out of scope.

# File hosts
This is the inventory file, that has the targets where you want to install SpamScope.
There is only a group **develop** with only a test server. You should change the target server with your target/targets (a line for target).
These are the parameters that I used to test the playbooks on my Debian virtual machine:

```
ansible_host=192.168.0.150 
ansible_connection=ssh 
ansible_port=22 
ansible_user=debian 
ansible_ssh_pass=screencast 
ansible_become_pass=screencast
```

Then there are others parameters for Apache Storm and all SpamScope requirements. I put all of them in **all:vars** section of inventory, but you can use `host_vars` or `group_vars`. [See here](http://docs.ansible.com/ansible/latest/user_guide/intro_inventory.html) for more details.
For first time you could use this inventory.

These are all parameters:

```
bin_path="/usr/local/bin"
install_path="/opt"

# Apache Storm
distro_name="apache-storm-1.2.1"
apache_storm_mirror="http://it.apache.contactlab.it/storm"
file_distro_name="{{ distro_name }}.tar.gz"
storm_url="{{ apache_storm_mirror }}/{{ distro_name }}/{{ file_distro_name }}"
delay=30
storm_path="{{ install_path }}/storm"

# Apache Storm - storm.yaml file
storm_log_dir=/var/log/storm
storm_local_dir=/var/lib/storm
worker_heap_memory_mb=2048
topology_worker_max_heap_size_mb=1024

# Apache Tika
apache_tika_version="1.16"
apache_tika_url="https://archive.apache.org/dist/tika/tika-app-{{ apache_tika_version }}.jar"

# Faup
faup_path="/opt/faup"
faup_repo="https://github.com/stricaud/faup.git"

# Lein
lein_url="https://raw.githubusercontent.com/technomancy/leiningen/stable/bin/lein"

# rarlinux
rarlinux_filename="rarlinux-x64-5.5.0.tar.gz"
rarlinux_url="https://www.rarlab.com/rar/{{ rarlinux_filename }}"

# SpamScope
spamscope_version="develop"
spamscope_repo="https://github.com/SpamScope/spamscope.git"
spamscope_path="/opt/spamscope"
spamscope_conf_path="/etc/spamscope"
```

I don't explain all of them, but only those parameters that are important:
 * `distro_name` if you want upgrade Apache Storm change version to;
 * `worker_heap_memory_mb` to give more memory to run Apache Storm;
 * `topology_worker_max_heap_size_mb` limit the heap space of SpamScope topology;
 * `apache_tika_version` is the version of Apache Tika and it's useful if you want upgrade this tool.

# Playbooks
There are two playbooks to install SpamScope:
 - [00_apache_storm_install.yml](./00_apache_storm_install.yml): this playbook installs Apache Storm
 - [01_spamscope_install.yml](./01_spamscope_install.yml): this playbook installs SpamScope

You can install both with [install.yml](./install.yml).

## 00_apache_storm_install.yml
The list of tasks is:

```
  play #1 (develop): Install Apache Storm       TAGS: []
    tasks:
      Install all system dependencies for Apache Storm  TAGS: []
      Make sure that all Apache Storm folders exist     TAGS: []
      Download Apache Storm in local    TAGS: []
      Copy Apache Storm on server target        TAGS: []
      Unarchive Apache Storm file archive       TAGS: []
      Remove Apache Storm file archive  TAGS: []
      Rename downloaded Apache Storm folder     TAGS: []
      Copy configuration file storm.yaml        TAGS: []
      Add Apache Storm bin in $PATH and environment variable    TAGS: []
      Make Apache Storm units files     TAGS: []
      Enable and start Apache Storm units files TAGS: []
      Wait for Apache Storm is up       TAGS: []
```

## 01_spamscope_install.yml
The list of tasks is:

```
  play #1 (develop): Install SpamScope  TAGS: []
    tasks:
      Install lein      TAGS: []
      Install all SpamScope system dependencies TAGS: []
      Install virtualenv        TAGS: []
      Make SpamScope worker folders     TAGS: []
      Copy SpamScope main configuration file    TAGS: []
      Copy others SpamScope configuration files TAGS: []
      Download Apache Tika in local     TAGS: []
      Copy Apache Tika on server        TAGS: []
      Clone Faup        TAGS: [git]
      Build Faup        TAGS: []
      Download rarlinux TAGS: []
      Copy rarlinux on server   TAGS: []
      Unarchive rarlinux file archive   TAGS: []
      Remove rarlinux file archive      TAGS: []
      Make rarlinux symbolic links in bin path  TAGS: []
      Clone SpamScope repository        TAGS: [git]
      Install SpamScope TAGS: []
      Install SpamScope requirements optional   TAGS: []
      Enable SpamScope environment variable     TAGS: []

```

With this playbook you will install a main SpamScope configuration path to test your installation:
 * in `/var/lib/spamscope/moved` SpamScope moves the email analyzed
 * in `/var/lib/spamscope/failed` SpamScope moves the email that it couldn't analyze
 * in `/var/lib/spamscope/output` SpamScope save the output, if you use spamscope_debug topology, that saves the output on filesystem
 * in `/var/log/spamscope` SpamScope puts the Python logs

The main configuration file in this installation enable only _Apache Tika_ and _SpamAssassin_.

# Installation
You can use `ansible` folder to install SpamScope.

First you should install requirements:

```
$ cd ansible
$ virtualenv venv-ansible
$ source venv-ansible/bin/activate
$ pip install -r requirements.txt
```

Now you have Ansible. Then change the file `hosts` with your data and run the playbook:

```
$ ansible-playbook install.yml
```

After that you have Apache Storm and SpamScope installed. Check the url `http://server_ip:8080`, that gives you the overview of Apache Storm.

But SpamScope isn't up because you must submit a topology. From Apache Storm concepts:

_The logic for a realtime application is packaged into a Storm topology. A Storm topology is analogous to a MapReduce job. One key difference is that a MapReduce job eventually finishes, whereas a topology runs forever (or until you kill it, of course). A topology is a graph of spouts and bolts that are connected with stream groupings._

Now we can submit the `spamscope_debug` topology using a custom command line tool that comes with SpamScope `spamscope-topology`.

```
$ cd /opt/spamscope # or your SpamScope path
$ spamscope-topology submit -g spamscope_debug -p 100 -t 30
```

The command that I want to exec is `spamscope-topology submit`, for more details read the guide inside [spamscope/src/cli/](../src/cli/README.md) folder.

Now SpamScope is up and running. You can navigate url `http://server_ip:8080` and you will see `spamscope_debug` under `Topology Summary` section.

_In this playbook there isn't the Thug installation, that you can install following Thug guide._
