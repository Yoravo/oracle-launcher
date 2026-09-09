import os
import sys
import oci
import requests

COMPARTMENT_ID = "ocid1.tenancy.oc1..aaaaaaaaky6oosf4dxtjdg3en6hauj4ss6fuen5ngqgjef55yfqrou7eiyda"
SUBNET_ID = "ocid1.subnet.oc1.ap-batam-1.aaaaaaaaqxcpjee6p43f6h4n7i436edytks7mbwfavqb6f7vrqrjvbcg3ffa"
IMAGE_ID = "ocid1.image.oc1.ap-batam-1.aaaaaaaaa637svxqycwi27xoxze75c54npn5cyute6dsfi6vdfz6gtnrfvya"
AD = "aMPn:AP-BATAM-1-AD-1"
SHAPE = "VM.Standard.A1.Flex"
OCPUS = 1
MEMORY_IN_GBS = 6
DISPLAY_NAME = "finance-tracker-vm"

def send_notification(subject, message):
    email = os.environ.get("NOTIFICATION_EMAIL")
    topic = os.environ.get("NTFY_TOPIC")
    if not topic or not email:
        return
    headers = {
        "Title": subject,
        "Email": email
    }
    requests.post(f"https://ntfy.sh/{topic}", data=message.encode("utf-8"), headers=headers)

config = oci.config.from_file(os.path.expanduser("~/.oci/config"))
compute_client = oci.core.ComputeClient(config)

existing = compute_client.list_instances(
    compartment_id=COMPARTMENT_ID,
    display_name=DISPLAY_NAME,
    lifecycle_state="RUNNING"
).data

if existing:
    print("Instance sudah aktif. Selesai.")
    sys.exit(0)

ssh_key = os.environ.get("SSH_PUBLIC_KEY")
launch_details = oci.core.models.LaunchInstanceDetails(
    compartment_id=COMPARTMENT_ID,
    availability_domain=AD,
    shape=SHAPE,
    display_name=DISPLAY_NAME,
    shape_config=oci.core.models.LaunchInstanceShapeConfigDetails(
        ocpus=OCPUS,
        memory_in_gbs=MEMORY_IN_GBS
    ),
    source_details=oci.core.models.InstanceSourceViaImageDetails(
        image_id=IMAGE_ID
    ),
    create_vnic_details=oci.core.models.CreateVnicDetails(
        subnet_id=SUBNET_ID,
        assign_public_ip=True
    ),
    metadata={
        "ssh_authorized_keys": ssh_key
    }
)

try:
    print("Trying to launch instance...")
    response = compute_client.launch_instance(launch_details)
    print("SUCCESS! Instance created.")
    send_notification(
        "Oracle VM Batam Berhasil Dibuat!",
        f"Instance {DISPLAY_NAME} berhasil dibuat di region Batam.\nStatus: PROVISIONING / RUNNING."
    )
except oci.exceptions.ServiceError as e:
    if "OutOfCapacity" in e.code or "capacity" in e.message.lower():
        print("Out of capacity. Coba lagi jadwal berikutnya.")
        sys.exit(0)
    else:
        print(f"Error: {e.code} - {e.message}")
        sys.exit(1)
