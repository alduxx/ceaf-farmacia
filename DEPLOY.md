# Guia de Deploy - CEAF Farmácia

Este guia explica como instalar e configurar a aplicação CEAF Farmácia em uma nova máquina utilizando Gunicorn e Nginx para produção.

## Pré-requisitos

- Ubuntu/Debian 20.04+ ou CentOS/RHEL 8+
- Acesso root ou usuário com privilégios sudo
- Conexão com a internet
- Domínio configurado (opcional, mas recomendado)

## Instalação Automática

### Opção 1: Script de Deploy Automático

```bash
# Clone o repositório
git clone https://github.com/user/ceaf-farmacia.git
cd ceaf-farmacia

# Execute o script de deploy (como root ou com sudo)
sudo ./deploy.sh
```

O script automaticamente:
- Instala todas as dependências do sistema
- Cria usuário dedicado para a aplicação
- Configura o ambiente Python
- Instala e configura Nginx
- Configura o serviço systemd
- Inicializa os dados da aplicação

## Instalação Manual

### 1. Preparar o Sistema

```bash
# Atualizar pacotes do sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependências do sistema
sudo apt install -y python3 python3-pip python3-venv nginx git curl

# Criar usuário para a aplicação
sudo useradd --system --shell /bin/bash --home /opt/farmacia --create-home farmacia
```

### 2. Configurar a Aplicação

```bash
# Clonar o repositório
sudo git clone https://github.com/user/ceaf-farmacia.git /opt/farmacia
sudo chown -R farmacia:farmacia /opt/farmacia

# Criar estrutura de diretórios
sudo -u farmacia mkdir -p /opt/farmacia/{logs,data,cache}

# Configurar ambiente Python
cd /opt/farmacia
sudo -u farmacia python3 -m venv venv
sudo -u farmacia venv/bin/pip install --upgrade pip
sudo -u farmacia venv/bin/pip install -r requirements.txt
sudo -u farmacia venv/bin/pip install gunicorn
```

### 3. Configurar Variáveis de Ambiente

```bash
sudo -u farmacia tee /opt/farmacia/.env << EOF
FLASK_ENV=production
FLASK_APP=src.app:app
PYTHONPATH=/opt/farmacia/src
# Adicione suas chaves de API:
# OPENAI_API_KEY=sua_chave_openai
# ANTHROPIC_API_KEY=sua_chave_anthropic
EOF
```

### 4. Configurar Systemd Service

```bash
# Copiar arquivo de serviço
sudo cp /opt/farmacia/farmacia.service /etc/systemd/system/

# Habilitar e iniciar o serviço
sudo systemctl daemon-reload
sudo systemctl enable farmacia
sudo systemctl start farmacia
```

### 5. Configurar Nginx

```bash
# Remover site padrão
sudo rm -f /etc/nginx/sites-enabled/default

# Copiar configuração do site
sudo cp /opt/farmacia/nginx.conf /etc/nginx/sites-available/farmacia

# Editar domínio na configuração (substituir 'your-domain.com')
sudo sed -i 's/your-domain.com/seu-dominio.com/g' /etc/nginx/sites-available/farmacia

# Habilitar site
sudo ln -s /etc/nginx/sites-available/farmacia /etc/nginx/sites-enabled/

# Testar configuração e reiniciar
sudo nginx -t
sudo systemctl restart nginx
```

### 6. Inicializar Dados

```bash
# Executar scraping inicial
cd /opt/farmacia
sudo -u farmacia venv/bin/python scripts/scrape_data.py
```

## Configurações de Produção

### Configuração de SSL/HTTPS

1. **Usando Certbot (Let's Encrypt) - Recomendado:**

```bash
# Instalar certbot
sudo apt install certbot python3-certbot-nginx

# Obter certificado
sudo certbot --nginx -d seu-dominio.com -d www.seu-dominio.com

# Verificar renovação automática
sudo certbot renew --dry-run
```

2. **Certificado próprio:**
   - Descomente e configure as seções HTTPS no arquivo `nginx.conf`
   - Adicione os caminhos para seus arquivos de certificado

### Configuração de Firewall

```bash
# UFW (Ubuntu)
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable

# iptables (alternativa)
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT
```

### Monitoramento e Logs

```bash
# Ver logs da aplicação
sudo journalctl -u farmacia -f

# Ver logs do Nginx
sudo tail -f /var/log/nginx/farmacia_access.log
sudo tail -f /var/log/nginx/farmacia_error.log

# Ver logs do Gunicorn
sudo tail -f /opt/farmacia/logs/gunicorn_error.log
```

### Backup Automático

Crie um script de backup em `/opt/farmacia/backup.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/opt/backups/farmacia"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup dos dados
tar -czf "$BACKUP_DIR/farmacia_data_$DATE.tar.gz" /opt/farmacia/data/
tar -czf "$BACKUP_DIR/farmacia_cache_$DATE.tar.gz" /opt/farmacia/cache/

# Manter apenas os últimos 7 dias
find $BACKUP_DIR -name "farmacia_*" -mtime +7 -delete

# Agendar no cron (executar diariamente às 2:00)
# 0 2 * * * /opt/farmacia/backup.sh
```

## Gerenciamento do Serviço

### Comandos Essenciais

```bash
# Iniciar serviço
sudo systemctl start farmacia

# Parar serviço
sudo systemctl stop farmacia

# Reiniciar serviço
sudo systemctl restart farmacia

# Verificar status
sudo systemctl status farmacia

# Ver logs em tempo real
sudo journalctl -u farmacia -f

# Recarregar configuração sem parar
sudo systemctl reload farmacia
```

### Atualizações da Aplicação

```bash
# Parar serviço
sudo systemctl stop farmacia

# Atualizar código
cd /opt/farmacia
sudo -u farmacia git pull

# Atualizar dependências (se necessário)
sudo -u farmacia venv/bin/pip install -r requirements.txt

# Reiniciar scraping (se necessário)
sudo -u farmacia venv/bin/python scripts/scrape_data.py

# Reiniciar serviço
sudo systemctl start farmacia
```

## Solução de Problemas

### Aplicação não inicia

```bash
# Verificar logs de erro
sudo journalctl -u farmacia -n 50

# Verificar configuração do Gunicorn
sudo -u farmacia /opt/farmacia/venv/bin/gunicorn --check-config /opt/farmacia/gunicorn.conf.py

# Testar aplicação manualmente
cd /opt/farmacia
sudo -u farmacia venv/bin/python src/app.py
```

### Nginx não serve conteúdo

```bash
# Testar configuração
sudo nginx -t

# Verificar logs
sudo tail -f /var/log/nginx/error.log

# Verificar se a aplicação está respondendo
curl http://localhost:5000
```

### Performance e Recursos

```bash
# Monitorar uso de recursos
htop
sudo netstat -tlnp | grep :5000
sudo lsof -i :5000

# Ajustar número de workers Gunicorn
# Editar /opt/farmacia/gunicorn.conf.py
# Reiniciar serviço após mudanças
```

## Configurações de Segurança

### Restrições de Acesso

1. **Configurar fail2ban:**

```bash
sudo apt install fail2ban

# Configurar para Nginx
sudo tee /etc/fail2ban/jail.d/nginx.conf << EOF
[nginx-http-auth]
enabled = true
port = http,https
logpath = /var/log/nginx/farmacia_error.log

[nginx-noscript]
enabled = true
port = http,https
logpath = /var/log/nginx/farmacia_access.log
EOF

sudo systemctl restart fail2ban
```

2. **Configurar rate limiting no Nginx:**

Adicione ao arquivo de configuração do Nginx:

```nginx
http {
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/m;
    
    server {
        location /search {
            limit_req zone=api burst=5 nodelay;
            # resto da configuração
        }
    }
}
```

### Atualizações de Segurança

```bash
# Agendar atualizações automáticas
sudo apt install unattended-upgrades

# Configurar
sudo dpkg-reconfigure -plow unattended-upgrades
```

## Checklist de Deploy

- [ ] Sistema operacional atualizado
- [ ] Dependências instaladas
- [ ] Usuário da aplicação criado
- [ ] Código clonado e permissões configuradas
- [ ] Ambiente Python configurado
- [ ] Variáveis de ambiente definidas
- [ ] Serviço systemd configurado e funcionando
- [ ] Nginx configurado e funcionando
- [ ] SSL/HTTPS configurado
- [ ] Firewall configurado
- [ ] Backup configurado
- [ ] Monitoramento configurado
- [ ] Teste de funcionalidade realizado

## Suporte

Para problemas específicos:
1. Verifique os logs da aplicação
2. Consulte a documentação do projeto
3. Abra uma issue no repositório

---

**Importante:** Sempre teste as mudanças em um ambiente de desenvolvimento antes de aplicar em produção.