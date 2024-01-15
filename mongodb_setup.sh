sudo su

apt-get install gnupg curl

curl -fsSL https://pgp.mongodb.com/server-7.0.asc | gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor

echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list

apt-get update

apt-get install -y mongodb-org

systemctl start mongod

#gcp copy
gsutil cp gs://masterdata2/setup/mongodb-bi-linux-x86_64-ubuntu2004-v2.14.12.tgz /home/cloudeusz/mongodb-bi.tgz

tar -xvzf mongodb-bi.tgz

#cos tam trzeba zrobic

mongosqld --addr 0.0.0.0:3307
setsid mongosqld --addr 0.0.0.0:3307 --logPath /logs/mongosqld.log