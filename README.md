# api-system-fitsi
Code on local can use this code deploy on gcp <br/>
And don't forget requirements.txt

```powershell
pip install -r requirements.txt
```

Credential Key can create on gcp and change path in code
```python
PATH = os.path.join(os.getcwd() , '###.json') # change path this line
```

Structure function api system fitsi
1. Login System
    - signup
    - signin
    - save log login
2. History System
    - filter user relation with login
    - calculate time spent