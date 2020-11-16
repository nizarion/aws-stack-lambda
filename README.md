# archimedes-tech-test 
## readme placeholder (Nizar Almesri)

This is my solution to the archimedes-tech-test.

## Stack

Uses AWS lambda, DynamoDB, Api gateway and S3

- The data is injested by the api_receiver.
    - api endpoint using aws API gateway
    - lambda written in python to prepare amd store data
- Stored in DynamoDb, 2 tables calls & operators
- matcher_call_operator lambda can be triggered by either an API event or on schedule using CloudWatch Events, only API event is implemented
    - lambda will prepare every call by enriching it with the requested information
    - store the output report in a csv in S3
    - if the enriched data need to be accessed more often then the output would be stored in a Database Table and the report would be presented by another function/lambda

## Details/Notes

I have chosen to have a single api endpoint for both calls and operators registration because of the existance of the type in both of them and the similarity of the source data structures.

While ingesting the data the part that was harder was the ingesting the float, since DynamoDB does not have floats.

For the prefix it was assumed that only the first digit after the country code is important. This is purely based on the examples and does not include more complex prefixes (e.g. 2300 could mean that calls with 2300-2399 belong to this operator)
