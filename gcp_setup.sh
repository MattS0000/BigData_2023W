gcloud compute instances create nifi \
    --project=gcc2023-385607 \
    --zone=europe-central2-a \
    --machine-type=e2-medium \
    --network-interface=network-tier=PREMIUM,stack-type=IPV4_ONLY,subnet=default \
    --maintenance-policy=MIGRATE \
    --provisioning-model=STANDARD \
    --service-account=891597161963-compute@developer.gserviceaccount.com \
    --scopes=https://www.googleapis.com/auth/devstorage.read_only,https://www.googleapis.com/auth/logging.write,https://www.googleapis.com/auth/monitoring.write,https://www.googleapis.com/auth/servicecontrol,https://www.googleapis.com/auth/service.management.readonly,https://www.googleapis.com/auth/trace.append \
    --tags=http-server,https-server \
    --create-disk=auto-delete=yes,boot=yes,device-name=nifi,image=projects/ubuntu-os-cloud/global/images/ubuntu-2004-focal-v20231213,mode=rw,size=10,type=projects/gcc2023-385607/zones/europe-central2-a/diskTypes/pd-standard \
    --no-shielded-secure-boot \
    --shielded-vtpm \
    --shielded-integrity-monitoring \
    --labels=goog-ec-src=vm_add-gcloud \
    --reservation-affinity=any

gcloud compute ssh --zone "europe-central2-a" "nifi" --project "gcc2023-385607"
#in the ssh
gsutil cp gs://nifidata/nifi_setup.sh /home/cloud2023ezproject/nifi_setup.sh
nifi_setup.sh
exit

gcloud compute instances create mongodb \
    --project=gcc2023-385607 \
    --zone=europe-central2-a \
    --machine-type=e2-medium \
    --network-interface=network-tier=PREMIUM,stack-type=IPV4_ONLY,subnet=default \
    --maintenance-policy=MIGRATE \
    --provisioning-model=STANDARD \
    --service-account=891597161963-compute@developer.gserviceaccount.com \
    --scopes=https://www.googleapis.com/auth/devstorage.read_only,https://www.googleapis.com/auth/logging.write,https://www.googleapis.com/auth/monitoring.write,https://www.googleapis.com/auth/servicecontrol,https://www.googleapis.com/auth/service.management.readonly,https://www.googleapis.com/auth/trace.append \
    --tags=http-server,https-server \
    --create-disk=auto-delete=yes,boot=yes,device-name=nifi,image=projects/ubuntu-os-cloud/global/images/ubuntu-2004-focal-v20231213,mode=rw,size=10,type=projects/gcc2023-385607/zones/europe-central2-a/diskTypes/pd-standard \
    --no-shielded-secure-boot \
    --shielded-vtpm \
    --shielded-integrity-monitoring \
    --labels=goog-ec-src=vm_add-gcloud \
    --reservation-affinity=any
	
gcloud compute ssh --zone "europe-central2-a" "mongodb" --project "gcc2023-385607"
#in the ssh
gsutil cp gs://nifidata/mongodb_setup.sh /home/cloud2023ezproject/mongodb_setup.sh
mongodb_setup.sh
exit