# Octopuslabs Code Challenge

## Prerequisites

Google App Engine SDK installed in your computer

## Install

```
git clone https://github.com/eduardoferrandezr/octopuslabs-code-challenge.git

cd octopuslabs-code-challenge

mkdir lib

pip install -t lib tornado

pip install -t lib beautifulsoup4

pip install -t lib pycrypto
```

## Use
```
dev_appserver.py .
````

## Note on storing the keys

The best way to safely store and manage the private keys would be on the environment, not in the application, so they could be retrieved using

```python
  rsakey = os.environ.get('PRIVATE_RSA_KEY')
  salt = os.environ.get('SALT')
```

This way, only people with access to the production servers can see and manage the keys

