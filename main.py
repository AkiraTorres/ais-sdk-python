import boto3
import os
from time import sleep

# Credenciais do usuário IAM
aws_access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
region_name = os.environ.get('AWS_DEFAULT_REGION')
instance_name = 'ais-instance'

# Inicializa a conexão com o serviço EC2 usando as credenciais IAM
ec2 = boto3.resource(
    'ec2',
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    region_name=region_name
)

client = boto3.client(
    'ec2',
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    region_name=region_name
)

# Função CREATE - Inicia uma instância EC2
def start_instance():
    instance = ec2.create_instances(
        ImageId='ami-0f16d0d3ac759edfa',
        MinCount=1,
        MaxCount=1,
        InstanceType='t2.micro',
        KeyName='aws_debian',
        TagSpecifications = [
            {
                'ResourceType': 'instance',
                'Tags': [
                    {
                        'Key': 'Name',
                        'Value': instance_name
                    }
                ]
            }
        ]
    )

    instance_id = instance[0].id
    print(f'Instância iniciada com ID: {instance_id} e nome {instance_name}')

    return instance_id


# Função RETRIEVE - Lista todas as instâncias e suas informações
def list_instances():
    response = client.describe_instances()

    instances_info = []

    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            # print(instance)
            instance_id = instance['InstanceId']
            try:
                name = instance['Tags'][0]['Value']
            except:
                name = 'Nenhum nome'
            state = instance['State']['Name']
            ip_address = instance.get('PublicIpAddress', 'Nenhum IP público')
            launch_time = instance['LaunchTime']

            info = {
                'Name': name,
                'Instance ID': instance_id,
                'State': state,
                'Public IP': ip_address,
                'Launch Time': launch_time
            }

            instances_info.append(info)
            print(info)

    return instances_info


# Função UPDATE - Atualiza algum parâmetro da instância (ex: tipo de instância)
def update_instance_type(instance_id, new_instance_type):
    # Primeiro precisamos parar a instância para atualizar o tipo
    client.stop_instances(InstanceIds=[instance_id])
    print(f'Parando a instância {instance_id}...')

    waiter = client.get_waiter('instance_stopped')
    waiter.wait(InstanceIds=[instance_id])
    print(f'A instância {instance_id} foi parada.')

    # Agora atualizamos o tipo de instância
    client.modify_instance_attribute(InstanceId=instance_id, InstanceType={'Value': new_instance_type})
    print(f'Tipo de instância atualizado para {new_instance_type}.')

    # Finalmente, reiniciamos a instância
    client.start_instances(InstanceIds=[instance_id])
    print(f'Reiniciando a instância {instance_id}...')

    waiter = client.get_waiter('instance_running')
    waiter.wait(InstanceIds=[instance_id])
    print(f'A instância {instance_id} está executando novamente com o tipo {new_instance_type}.')


# Função DELETE - Termina uma instância
def terminate_instance(instance_id):
    try:
        # Tenta terminar a instância
        response = client.terminate_instances(InstanceIds=[instance_id])
        print(f'Terminando a instância {instance_id}...')

        # Usar um waiter para aguardar a instância ser terminada
        waiter = client.get_waiter('instance_terminated')
        waiter.wait(InstanceIds=[instance_id])
        print(f'Instância {instance_id} foi terminada.')

    except Exception as e:
        print(f'Erro ao tentar terminar a instância {instance_id}: {e}')



# Fluxo principal (exemplo de uso)
if __name__ == '__main__':
    # CREATE: Inicia uma nova instância
    instance_id = start_instance()

    # Pausa para garantir que a instância esteja inicializada
    sleep(10)

    # RETRIEVE: Lista todas as instâncias e suas informações
    list_instances()

    # UPDATE: Atualiza o tipo da instância
    # update_instance_type(instance_id, 't2.small')

    # DELETE: Termina a instância
    terminate_instance(instance_id)
