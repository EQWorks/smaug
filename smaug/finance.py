# cloudwatch logs insights query
# acting on logs group /aws/lambda/smaug-dev-increment
# TODO: see if logs group can be inferred from serverless/cloudformation config
query = '''
    fields @message
        | filter @message like "smaug#id"
        | parse @message /\[(?<level>\S+)\]\s+(?<ts>\S+)\s+(?<rid>\S+)\s+(?<msg>\S+)/
        | parse msg /smaug#id#(?<id>\S+)#whitelabel#(?<whitelabel>\S+)#customer#(?<customer>\S+)#key#(?<key>\S+)#n#(?<calls>\S+)/
        | parse id /(?<endpoint>[^\s\?\#]+)(\?(?<query>\S+))?/
        | parse endpoint /(?<stage>[^\s\/]+)(?<api>\S+)?/
        | stats sum(calls) as total_calls by whitelabel, customer, stage, api
'''
