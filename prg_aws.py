#Libraries
import os
import boto3
import requests
import time
from passwd_gen import password_generator

try:
	import paramiko
except ModuleNotFoundError:
	os.system('pip3 install paramiko')
	import paramiko

# Variables
WP_DB_HOST = 'localhost'
WP_DB_NAME = 'wp_database'
WP_DB_USER = 'wp_user'
WP_DB_PASS = 'wikipass' #The WP DB pass is generated by a script
AWS_KEY_NAME = 'MaPaire'
AWS_INSTANCE = 't3.nano'
AWS_AMI_ID = 'ami-05829248ffee66250' #Note: The program was developped for Debian 9

# Functions
def install_apache2():
	in_, out_, err_ = ssh.exec_command("sudo apt-get update -y && sudo apt-get upgrade -y && sudo apt-get install apache2 -y")
	out_.channel.recv_exit_status()

	os.system("touch Gen_Files/01-{}.conf".format(url))

	vhost_non_conf = open('Ressources/vhost.conf','r')
	vhost_conf = open('Gen_Files/01-{}.conf'.format(url), 'w')

	line = 'not_empty'

	while line:
		line = vhost_non_conf.readline()
		vhost_conf.write(line.format(APACHE_LOG_DIR='{APACHE_LOG_DIR}', votre_url=url))

	vhost_conf.close()

	sftp.put('Gen_Files/01-{}.conf'.format(url), '/home/admin/01-{}.conf'.format(url))
	time.sleep(1)

	in_, out_, err_ = ssh.exec_command("sudo cp /home/admin/01-{}.conf /etc/apache2/sites-available/".format(url))
	out_.channel.recv_exit_status()
	in_, out_, err_ = ssh.exec_command("sudo mkdir /var/www/html/{}/".format(url))
	out_.channel.recv_exit_status()
	in_, out_, err_ = ssh.exec_command("sudo cp /var/www/html/index.html /var/www/html/{}".format(url))
	out_.channel.recv_exit_status()
	in_, out_, err_ = ssh.exec_command("sudo a2dissite 000-default")
	out_.channel.recv_exit_status()
	in_, out_, err_ = ssh.exec_command("sudo a2ensite 01-{}".format(url))
	out_.channel.recv_exit_status()
	in_, out_, err_ = ssh.exec_command("sudo systemctl reload apache2")
	out_.channel.recv_exit_status()

	print('Conf Apache OK.')

def install_php():
	in_, out_, err_ = ssh.exec_command("sudo apt-get install php-fpm -y")
	out_.channel.recv_exit_status()
	
	in_, out_, err_ = ssh.exec_command("sudo a2enmod proxy_fcgi setenvif")
	out_.channel.recv_exit_status()

	in_, out_, err_ = ssh.exec_command("sudo a2enconf php7.0-fpm")
	out_.channel.recv_exit_status()

	in_, out_, err_ = ssh.exec_command("sudo systemctl restart apache2")
	out_.channel.recv_exit_status()

	print('Conf PHP OK.')

def install_mysql():
	in_, out_, err_ = ssh.exec_command("sudo apt-get install mysql-server -y && sudo apt-get install php7.0-mysql -y")
	out_.channel.recv_exit_status()

	sftp.put('Ressources/bdd.sql', '/home/admin/bdd.sql')
	time.sleep(1)

	print("Conf MySQL OK.")

def install_wp():
	in_, out_, err_ = ssh.exec_command("sudo wget https://wordpress.org/latest.tar.gz -P /var/www/html/{}".format(url))
	out_.channel.recv_exit_status()
	in_, out_, err_ = ssh.exec_command("sudo tar zxvf /var/www/html/{}/latest.tar.gz -C /var/www/html/{}/".format(url, url))
	out_.channel.recv_exit_status()

	secret_key = 'https://api.wordpress.org/secret-key/1.1/salt/'
	r = requests.post(secret_key)

	os.system("touch Gen_Files/wp-config.php")

	wp_non_conf = open('Ressources/wp-config.txt', 'r')
	wp_conf = open('Gen_Files/wp-config.php', 'w')

	line = 'not_empty'

	while line:
		line = wp_non_conf.readline()
		wp_conf.write(line.format(db_name=WP_DB_NAME,db_user=WP_DB_USER,db_mdp=WP_DB_PASS,key_secret=r.text))

	wp_conf.close()
	sftp.put('Gen_Files/wp-config.php', '/home/admin/wp-config.php')
	time.sleep(1)

	in_, out_, err_ = ssh.exec_command("sudo cp /home/admin/wp-config.php /var/www/html/{}/wordpress/wp-config.php".format(url))
	out_.channel.recv_exit_status()

	in_, out_, err_ = ssh.exec_command("sudo mysql -u root < bdd.sql")
	out_.channel.recv_exit_status()

	print("Conf WP OK.")

def install_ssl():
	print('Please add this IP : {} to your A record for the domain {}'.format(ip, url))

	caract = input('If you can\'t do that, please answer \'c\' otherwise answer anything : ') 

	if caract != 'c':
		#SSL
		in_, out_, err_ = ssh.exec_command("sudo apt-get install letsencrypt -y")
		out_.channel.recv_exit_status()
		in_, out_, err_ = ssh.exec_command("sudo systemctl stop apache2")
		out_.channel.recv_exit_status()
		in_, out_, err_ = ssh.exec_command("sudo letsencrypt certonly --standalone --agree-tos --email admin@{site} -d {site} -d www.{site} --standalone-supported-challenges http-01".format(site=url))
		out_.channel.recv_exit_status()

		vhost_ssl_non_conf = open('Ressources/vhost_ssl.conf','r')
		vhost_ssl_conf = open('Gen_Files/01-{}.conf'.format(url), 'w')

		line = 'not_empty'

		while line:
			line = vhost_ssl_non_conf.readline()
			vhost_ssl_conf.write(line.format(APACHE_LOG_DIR='{APACHE_LOG_DIR}', votre_url=url, HTTPS='{HTTPS}', SERVER_NAME='{SERVER_NAME}', REQUEST_URI='{REQUEST_URI}'))

		vhost_ssl_conf.close()	

		sftp.put('Gen_Files/01-{}.conf'.format(url), '/home/admin/01-{}.conf'.format(url))
		time.sleep(1)

		in_, out_, err_ = ssh.exec_command("sudo cp /home/admin/01-{}.conf /etc/apache2/sites-available/".format(url))
		out_.channel.recv_exit_status()
		in_, out_, err_ = ssh.exec_command("sudo systemctl start apache2")
		out_.channel.recv_exit_status()
		in_, out_, err_ = ssh.exec_command("sudo a2enmod ssl")
		out_.channel.recv_exit_status()
		in_, out_, err_ = ssh.exec_command("sudo a2enmod rewrite")
		out_.channel.recv_exit_status()
		in_, out_, err_ = ssh.exec_command("sudo systemctl restart apache2")
		out_.channel.recv_exit_status()

		print("Conf SSL OK.")

	else:
		print("Conf SSL NOT OK.")

#Pre-start
os.system("rm -r Gen_Files/*")

#Beginning of the program
url = input('Enter the URL as \'example.com\' (without \'www\' or \'http(s)\'): ')

ssl = input('Do you want an HTTPS website ? (o/n): ').lower() # HTTPS is powered by LetsEncrypt

if ssl != 'o':
	ssl = 'n'

ec2 = boto3.resource('ec2')
# Create a new EC2 instance
instances = ec2.create_instances(
     ImageId=AWS_AMI_ID,
     MinCount=1,
     MaxCount=1,
     InstanceType=AWS_INSTANCE,
     KeyName=AWS_KEY_NAME
 )

instance = instances[0]

print("Please wait until the installation..")

# Wait for the instance to enter the running state
instance.wait_until_running()

# Reload the instance attributes
instance.load()

# Save the ip of the instance
ip = instance.public_ip_address

# Wait a bit for the instance's initialisation
time.sleep(5)

# SSH connection
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(str(ip), username='admin', key_filename='/home/user/Bureau/OS/MaPaire.pem')
sftp = ssh.open_sftp()

# APACHE
install_apache2()

#SSL
if ssl == 'o':
	install_ssl()

# PHP
install_php()

# MYSQL
install_mysql()

# WORDPRESS
install_wp()

# End of the SSH connection
ssh.close()

print('IP of your machine : ' + ip)# Display the public IP of the AWS instance
print('Please note that this is the password for the wordpress database: ' + WP_DB_PASS)# Display the BDD password. Please note it.

# End of the program