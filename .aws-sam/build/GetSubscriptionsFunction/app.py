import json
import boto3
import os
from decimal import Decimal

REGION = os.environ['REGION']
SUBSCRIPTIONS_TABLE = os.environ['SUBSCRIPTIONS_TABLE']
FUNDS_TABLE = os.environ['FUNDS_TABLE']

dynamodb = boto3.resource('dynamodb', region_name=REGION)
subscriptions_table = dynamodb.Table(SUBSCRIPTIONS_TABLE)  
funds_table = dynamodb.Table(FUNDS_TABLE)

def add_cors_headers(response):
    response['headers'] = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET',
        'Access-Control-Allow-Headers': 'Content-Type',
    }
    return response

def decimal_to_float(obj):
    """Convierte Decimal a float para la serialización JSON."""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Type {type(obj)} not serializable")

def get_user_subscriptions(user_id):
    """Obtiene las cuentas suscritas para un usuario."""
    subscriptions = []
    try:
        response = subscriptions_table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('PK').eq(user_id)
        )
        for item in response.get('Items', []):
            subscriptions.append({
                'fundId': item['SK'],  # Suponiendo que SK es el ID del fondo
                'amount': item.get('Amount', 0),  # Suponiendo que tienes un campo de monto
                'timestamp': item.get('Timestamp', ''),  # Fecha de suscripción, si existe
            })
    except Exception as e:
        print(f"Error al obtener suscripciones: {str(e)}")
    return subscriptions

def get_all_funds():
    """Obtiene todos los fondos disponibles."""
    funds = []
    try:
        response = funds_table.scan()
        for item in response.get('Items', []):
            funds.append({
                'fundId': item['PK'],  # Suponiendo que PK es el ID del fondo
                'name': item.get('Name', ''),  # Nombre del fondo, si existe
                'minimumInvestment': item.get('MinimumInvestment', 0),  # Monto mínimo de inversión, si existe
            })
    except Exception as e:
        print(f"Error al obtener fondos: {str(e)}")
    return funds

def main(event, context):
    user_id = event['pathParameters']['userId']
    
    user_subscriptions = get_user_subscriptions(user_id)
    all_funds = get_all_funds()
    
    # Crear un conjunto de IDs de fondos a los que el usuario está suscrito
    subscribed_funds = {sub['fundId'] for sub in user_subscriptions}
    
    # Filtrar los fondos no suscritos
    not_subscribed_funds = [fund for fund in all_funds if fund['fundId'] not in subscribed_funds]

    response = {
        'statusCode': 200,
        'body': json.dumps({
            'subscriptions': user_subscriptions,
            'notSubscribedFunds': not_subscribed_funds
        }, default=decimal_to_float)  # Aquí se aplica la función de conversión
    }
    
    return add_cors_headers(response)
