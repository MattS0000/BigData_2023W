# on the nifi vm not tested yet, take caution, https://www.youtube.com/watch?v=V6YVx_qDFnI
sudo su
apt update -y
apt install openjdk-8-jdk -y
wget https://archive.apache.org/dist/nifi/1.16.0/nifi-1.16.0-bin.tar.gz
tar -xzvf nifi-1.16.0-bin.tar.gz

gsutil cp gs://masterdata2/setup/nifi.properties /home/cloudeusz/nifi-1.16.0/conf/nifi.properties

./nifi-1.16.0/bin/nifi.sh start

gsutil cp gs://masterdata2/setup/favorable-bison-410912-684be13aba5c.json /home/cloudeusz/servicekey.json
exit
