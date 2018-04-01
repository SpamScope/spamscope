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

# Apache Storm parameters
distro_name="apache-storm-1.2.1"
apache_storm_mirror="http://it.apache.contactlab.it/storm"
file_distro_name="{{ distro_name }}.tar.gz"
storm_url="{{ apache_storm_mirror }}/{{ distro_name }}/{{ file_distro_name }}"
delay=30
storm_path="{{ install_path }}/storm"

# Apache Storm parameters - storm.yaml file
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

# SpamScope parameters
lein_url="https://raw.githubusercontent.com/technomancy/leiningen/stable/bin/lein"
```

I don't explain all of them, but only those parameters that are important.
If you want upgrade Apache Storm change version to `distro_name`.
To give more memory to run Apache Storm use `worker_heap_memory_mb`, while `topology_worker_max_heap_size_mb` limit the heap space of SpamScope topology.
`apache_tika_version` is the version of Apache Tika and it's useful if you want upgrade this tool.