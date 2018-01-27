*** Variables ***
${URL}    %{SOS_SERVER_URL}

*** Settings ***
Library  Collections
Library  RequestsLibrary

*** Test Cases ***

Get Root
  Create Session  sos  ${URL}
  ${resp}=  Get Request  sos  /
  Should Be Equal As Strings  ${resp.status_code}  200

Get Hostname
  Create Session  sos  ${URL}
  ${resp}=  Get Request  sos  /hostname
  Should Be Equal As Strings  ${resp.status_code}  200

Post New Order
  Create Session  sos  ${URL}
  &{data}=  Create Dictionary  name=John Smith  address=9684 Constitution Court  city=Chesapeake  state=VA  zipcode=23320  dueDate=01/01/2050  productType=Guitar
  &{headers}=  Create Dictionary  Content-Type=application/x-www-form-urlencoded
  ${resp}=  Post Request  sos  /sos/orders  data=${data}  headers=${headers}
  Should Be Equal As Strings  ${resp.status_code}  200
  Should Be Equal As Strings  ${resp.json()["name"]}  John Smith
  Should Be Equal As Strings  ${resp.json()["address"]}  9684 Constitution Court
  Should Be Equal As Strings  ${resp.json()["city"]}  Chesapeake
  Should Be Equal As Strings  ${resp.json()["state"]}  VA
  Should Be Equal As Strings  ${resp.json()["zipcode"]}  23320
  Should Be Equal As Strings  ${resp.json()["dueDate"]}  01/01/2050
  Should Be Equal As Strings  ${resp.json()["productType"]}  Guitar
  Set Suite Variable  ${ORDER_ID}  ${resp.json()["id"]}

Get New Order Details
  Create Session  sos  ${URL}
  ${resp}=  Get Request  sos  /sos/orders/${ORDER_ID}
  Should Be Equal As Strings  ${resp.status_code}  200
  Should Be Equal As Strings  ${resp.json()["order"]["name"]}  John Smith
  Should Be Equal As Strings  ${resp.json()["order"]["address"]}  9684 Constitution Court
  Should Be Equal As Strings  ${resp.json()["order"]["city"]}  Chesapeake
  Should Be Equal As Strings  ${resp.json()["order"]["state"]}  VA
  Should Be Equal As Strings  ${resp.json()["order"]["zipcode"]}  23320
  Should Be Equal As Strings  ${resp.json()["order"]["dueDate"]}  01/01/2050
  Should Be Equal As Strings  ${resp.json()["order"]["productType"]}  Guitar
  Should Be Equal As Strings  ${resp.json()["order"]["id"]}  ${ORDER_ID}

Post Bad Order
  Create Session  sos  ${URL}
  &{data}=  Create Dictionary  name=John Smith  address=9684 Constitution Court  city=Chesapeake  state=VA  zipcode=23320  dueDate=01/01/2000  productType=Guitar
  &{headers}=  Create Dictionary  Content-Type=application/x-www-form-urlencoded
  ${resp}=  Post Request  sos  /sos/orders  data=${data}  headers=${headers}
  Should Be Equal As Strings  ${resp.status_code}  400
  Should Be Equal As Strings  ${resp.json()["error"]}  due date is too early