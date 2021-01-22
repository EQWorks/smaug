# cloudwatch logs insights query
# acting on logs group /aws/lambda/smaug-dev-increment
# TODO: see if logs group can be inferred from serverless/cloudformation config
query = '''
    fields @message
    | filter @message like "smaug#id"
    # | filter @message not like "whitelabel#-1"
    | parse @message /\[(?<level>\S+)\]\s+(?<ts>\S+)\s+(?<rid>\S+)\s+(?<msg>\S+)/
    | parse msg /smaug#id#(?<id>\S+)#whitelabel#(?<whitelabel>\S+)#customer#(?<customer>\S+)#key#(?<key>\S+)#n#(?<calls>\S+)/
    | parse id /(?<api>\S+)\?(?<query>\S+)/
    | stats sum(calls) as total_calls by whitelabel, customer, api
'''
