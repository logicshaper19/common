# Common MuleSoft Connector Deployment Guide

This guide provides comprehensive instructions for deploying the Common MuleSoft Connector in enterprise environments.

## Prerequisites

### System Requirements
- **MuleSoft Runtime**: 4.4.x or later
- **Java**: 8 or later (11+ recommended)
- **Maven**: 3.6+ (for building from source)
- **Anypoint Studio**: 7.x or later (for development)

### Common API Requirements
- **API Access**: Valid Common API credentials
- **Network Access**: HTTPS connectivity to `api.common.co`
- **Authentication**: OAuth 2.0 client credentials
- **Company Setup**: Active Common platform account with company profile

## Deployment Options

### Option 1: Anypoint Exchange (Recommended)

1. **Download from Exchange**:
   ```bash
   # In Anypoint Studio
   # 1. Open Mule Palette
   # 2. Click "Search in Exchange"
   # 3. Search for "Common Supply Chain Connector"
   # 4. Click "Add to project"
   ```

2. **Configure Dependencies**:
   ```xml
   <!-- Automatically added to pom.xml -->
   <dependency>
       <groupId>com.common.connectors</groupId>
       <artifactId>common-mulesoft-connector</artifactId>
       <version>1.0.0</version>
       <classifier>mule-plugin</classifier>
   </dependency>
   ```

### Option 2: Manual JAR Installation

1. **Download Connector JAR**:
   ```bash
   # Download from Common's connector repository
   wget https://releases.common.co/connectors/mulesoft/common-mulesoft-connector-1.0.0-mule-plugin.jar
   ```

2. **Install in Anypoint Studio**:
   - Right-click project → "Install Connector from File"
   - Select the downloaded JAR file
   - Click "Install"

3. **Install in Standalone Mule**:
   ```bash
   # Copy to Mule installation
   cp common-mulesoft-connector-1.0.0-mule-plugin.jar $MULE_HOME/apps/your-app/lib/
   ```

### Option 3: Build from Source

1. **Clone Repository**:
   ```bash
   git clone https://github.com/common-co/mulesoft-connector.git
   cd mulesoft-connector
   ```

2. **Build Connector**:
   ```bash
   ./build.sh
   ```

3. **Install Built JAR**:
   ```bash
   # JAR will be in target/ directory
   cp target/common-mulesoft-connector-1.0.0-mule-plugin.jar $MULE_HOME/apps/your-app/lib/
   ```

## Configuration

### Environment-Specific Configuration

#### Development Environment
```properties
# dev-mule-app.properties
common.api.baseUrl=https://api-dev.common.co
common.api.clientId=dev-client-id
common.api.clientSecret=dev-client-secret
common.api.companyId=your-dev-company-uuid
common.api.timeout=30
common.api.maxRetries=3
common.api.debugMode=true
```

#### Staging Environment
```properties
# staging-mule-app.properties
common.api.baseUrl=https://api-staging.common.co
common.api.clientId=staging-client-id
common.api.clientSecret=staging-client-secret
common.api.companyId=your-staging-company-uuid
common.api.timeout=30
common.api.maxRetries=3
common.api.debugMode=false
```

#### Production Environment
```properties
# prod-mule-app.properties
common.api.baseUrl=https://api.common.co
common.api.clientId=${secure::common.api.clientId}
common.api.clientSecret=${secure::common.api.clientSecret}
common.api.companyId=${secure::common.api.companyId}
common.api.timeout=60
common.api.maxRetries=5
common.api.debugMode=false
```

### Secure Properties Configuration

1. **Create Secure Properties File**:
   ```bash
   # Create secure properties
   echo "common.api.clientId=your-production-client-id" > secure.properties
   echo "common.api.clientSecret=your-production-client-secret" >> secure.properties
   echo "common.api.companyId=your-production-company-uuid" >> secure.properties
   ```

2. **Encrypt Properties**:
   ```bash
   # Using Mule Secure Properties Tool
   java -cp $MULE_HOME/lib/mule-secure-properties-tool.jar \
        org.mule.tools.SecurePropertiesTool \
        string encrypt Blowfish CBC your-encryption-key "your-secret-value"
   ```

3. **Configure in Application**:
   ```xml
   <secure-properties:config name="Secure_Properties" 
                            file="secure.properties" 
                            key="${encryption.key}"/>
   ```

### Connection Configuration

```xml
<common:config name="Common_Config" doc:name="Common Config">
    <common:connection 
        baseUrl="${common.api.baseUrl}"
        clientId="${secure::common.api.clientId}"
        clientSecret="${secure::common.api.clientSecret}"
        companyId="${secure::common.api.companyId}"
        timeout="${common.api.timeout}"
        maxRetries="${common.api.maxRetries}"
        debugMode="${common.api.debugMode}" />
</common:config>
```

## Network Configuration

### Firewall Rules
```bash
# Outbound HTTPS access to Common API
# Allow: 443/tcp to api.common.co
# Allow: 443/tcp to auth.common.co (for OAuth)
```

### Proxy Configuration
```xml
<!-- If using HTTP proxy -->
<http:request-config name="HTTP_Request_Config">
    <http:request-connection 
        host="api.common.co" 
        port="443" 
        protocol="HTTPS"
        proxyHost="${proxy.host}"
        proxyPort="${proxy.port}"
        proxyUsername="${proxy.username}"
        proxyPassword="${proxy.password}"/>
</http:request-config>
```

### Load Balancer Configuration
```yaml
# For high-availability deployments
upstream common_api {
    server api.common.co:443;
    server api-backup.common.co:443 backup;
}

server {
    listen 443 ssl;
    server_name your-mule-app.company.com;
    
    location /api/common/ {
        proxy_pass https://common_api/;
        proxy_ssl_verify on;
        proxy_ssl_trusted_certificate /etc/ssl/certs/ca-certificates.crt;
    }
}
```

## Monitoring and Logging

### Application Logging
```xml
<!-- log4j2.xml configuration -->
<Configuration>
    <Appenders>
        <RollingFile name="CommonConnectorLog" 
                    fileName="logs/common-connector.log"
                    filePattern="logs/common-connector-%d{yyyy-MM-dd}-%i.log.gz">
            <PatternLayout pattern="%d{ISO8601} [%t] %-5level %logger{36} - %msg%n"/>
            <Policies>
                <TimeBasedTriggeringPolicy />
                <SizeBasedTriggeringPolicy size="100 MB"/>
            </Policies>
            <DefaultRolloverStrategy max="10"/>
        </RollingFile>
    </Appenders>
    
    <Loggers>
        <Logger name="com.common.connectors" level="INFO" additivity="false">
            <AppenderRef ref="CommonConnectorLog"/>
        </Logger>
    </Loggers>
</Configuration>
```

### Health Check Endpoint
```xml
<flow name="health-check-flow">
    <http:listener config-ref="HTTP_Listener_config" path="/health"/>
    
    <!-- Test Common API connectivity -->
    <try>
        <common:list-purchase-orders config-ref="Common_Config" 
                                   page="1" 
                                   perPage="1"/>
        <set-payload value='{"status": "healthy", "common_api": "connected"}'/>
        <on-error-continue>
            <set-payload value='{"status": "unhealthy", "common_api": "disconnected"}'/>
        </on-error-continue>
    </try>
</flow>
```

### Metrics Collection
```xml
<!-- Custom metrics for monitoring -->
<flow name="purchase-order-metrics">
    <scheduler>
        <scheduling-strategy>
            <fixed-frequency frequency="300000"/> <!-- 5 minutes -->
        </scheduling-strategy>
    </scheduler>
    
    <common:list-purchase-orders config-ref="Common_Config"/>
    
    <set-variable variableName="totalOrders" value="#[sizeOf(payload)]"/>
    <set-variable variableName="pendingOrders" value="#[sizeOf(payload filter $.status == 'pending')]"/>
    
    <!-- Send metrics to monitoring system -->
    <logger level="INFO" message="Metrics - Total Orders: #[vars.totalOrders], Pending: #[vars.pendingOrders]"/>
</flow>
```

## Performance Tuning

### Connection Pool Settings
```xml
<common:config name="Common_Config_Optimized">
    <common:connection 
        baseUrl="${common.api.baseUrl}"
        clientId="${secure::common.api.clientId}"
        clientSecret="${secure::common.api.clientSecret}"
        companyId="${secure::common.api.companyId}"
        timeout="60"
        maxRetries="5"
        debugMode="false" />
</common:config>
```

### Batch Processing Configuration
```xml
<flow name="batch-purchase-order-sync">
    <batch:job jobName="purchaseOrderBatch" maxFailedRecords="10">
        <batch:input>
            <common:list-purchase-orders config-ref="Common_Config" 
                                       perPage="100"/>
        </batch:input>
        
        <batch:process-records>
            <batch:step name="processStep">
                <!-- Process each purchase order -->
                <logger message="Processing PO: #[payload.id]"/>
            </batch:step>
        </batch:process-records>
        
        <batch:on-complete>
            <logger message="Batch completed - Successful: #[payload.successfulRecords], Failed: #[payload.failedRecords]"/>
        </batch:on-complete>
    </batch:job>
</flow>
```

## Security Best Practices

### 1. Credential Management
- Use secure properties for all credentials
- Rotate API credentials regularly
- Never log sensitive information
- Use environment-specific credentials

### 2. Network Security
- Use HTTPS only
- Implement proper firewall rules
- Consider VPN for sensitive environments
- Monitor network traffic

### 3. Access Control
- Implement role-based access control
- Use least privilege principle
- Audit API access regularly
- Monitor for unusual activity

### 4. Data Protection
- Encrypt data in transit and at rest
- Implement proper error handling
- Sanitize log outputs
- Follow data retention policies

## Troubleshooting

### Common Issues

#### Authentication Failures
```bash
# Check credentials
curl -X POST https://api.common.co/api/v1/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials&client_id=YOUR_CLIENT_ID&client_secret=YOUR_CLIENT_SECRET"
```

#### Connection Timeouts
```xml
<!-- Increase timeout values -->
<common:connection timeout="120" maxRetries="5" />
```

#### SSL Certificate Issues
```bash
# Add Common's certificate to Java truststore
keytool -import -alias common-api -file common-api.crt -keystore $JAVA_HOME/lib/security/cacerts
```

### Debug Mode
```xml
<!-- Enable debug logging -->
<common:connection debugMode="true" />
```

### Support Contacts
- **Technical Support**: support@common.co
- **Documentation**: https://docs.common.co/connectors/mulesoft
- **Status Page**: https://status.common.co
- **Emergency**: +1-555-COMMON-1 (24/7)

## Deployment Checklist

### Pre-Deployment
- [ ] Connector JAR installed
- [ ] Configuration properties set
- [ ] Credentials configured and tested
- [ ] Network connectivity verified
- [ ] SSL certificates installed
- [ ] Monitoring configured
- [ ] Logging configured
- [ ] Health checks implemented

### Post-Deployment
- [ ] Connectivity test passed
- [ ] Sample operations executed
- [ ] Error handling tested
- [ ] Performance metrics baseline established
- [ ] Monitoring alerts configured
- [ ] Documentation updated
- [ ] Team training completed
- [ ] Support contacts shared

## Maintenance

### Regular Tasks
- Monitor API usage and performance
- Review and rotate credentials quarterly
- Update connector version as needed
- Review and optimize configurations
- Monitor error rates and patterns
- Backup configuration files
- Test disaster recovery procedures

### Updates and Upgrades
- Subscribe to Common connector updates
- Test updates in staging environment
- Plan maintenance windows for upgrades
- Document configuration changes
- Train team on new features

This deployment guide ensures successful implementation of the Common MuleSoft Connector in enterprise environments with proper security, monitoring, and maintenance practices.
