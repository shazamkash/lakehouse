# Java Setup for Lakehouse Client

## The Issue

When using the full `LakehouseClient` (which includes Delta Lake operations), you may encounter this error:

```
java.lang.UnsupportedClassVersionError: org/apache/spark/launcher/Main has been compiled
by a more recent version of the Java Runtime (class file version 61.0), this version of
the Java Runtime only recognizes class file versions up to 55.0
```

**What this means:**
- PySpark 3.5+ requires Java 17 or higher
- Your system has Java 11 (or lower)
- The `DeltaManager` needs Java to submit jobs to the Spark cluster

## Solutions

You have **three options**:

### Option 1: Use SimpleLakehouseClient (Recommended for Remote Deployment)

**No Java required on your local machine!**

Use the lightweight client and run Delta operations on the server:

```python
from lakehouse_client import SimpleLakehouseClient

# This works without Java
client = SimpleLakehouseClient()

# Upload data (no Java needed)
s3_uri = client.upload_parquet('data.csv', 'raw-data', 'dataset')

# Query data (no Java needed)
results = client.query_to_dataframe("SELECT * FROM delta.main.default.my_table")
```

For Delta table creation, use the server-side script:

```bash
# On the remote server (10.16.36.36)
python server/create_delta_table.py \\
    s3a://raw-data/dataset.parquet \\
    main \\
    default \\
    my_table
```

See `examples/quickstart_no_java.py` for a complete example.

**Pros:**
- ✓ No Java installation needed
- ✓ Works from any client (Windows, Mac, Linux)
- ✓ Lighter weight
- ✓ Perfect for remote deployments

**Cons:**
- Must SSH to server to create Delta tables
- Less convenient for rapid development

---

### Option 2: Install Java 17+ Locally

If you want to use the full `LakehouseClient`, install Java 17:

#### Ubuntu/Debian

```bash
# Install Java 17
sudo apt update
sudo apt install openjdk-17-jdk

# Verify installation
java -version
# Should show: openjdk version "17.x.x"

# Set JAVA_HOME
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
export PATH=$JAVA_HOME/bin:$PATH

# Add to ~/.bashrc to make permanent
echo 'export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64' >> ~/.bashrc
echo 'export PATH=$JAVA_HOME/bin:$PATH' >> ~/.bashrc
```

#### macOS

```bash
# Using Homebrew
brew install openjdk@17

# Set JAVA_HOME
export JAVA_HOME=/opt/homebrew/opt/openjdk@17
export PATH=$JAVA_HOME/bin:$PATH

# Add to ~/.zshrc (or ~/.bash_profile)
echo 'export JAVA_HOME=/opt/homebrew/opt/openjdk@17' >> ~/.zshrc
echo 'export PATH=$JAVA_HOME/bin:$PATH' >> ~/.zshrc
```

#### Windows

1. Download Java 17 from: https://adoptium.net/
2. Install the MSI package
3. Add to system PATH:
   - System Properties → Environment Variables
   - Add `JAVA_HOME`: `C:\Program Files\Eclipse Adoptium\jdk-17.x.x`
   - Add to PATH: `%JAVA_HOME%\bin`

#### Verify Java Installation

```bash
java -version
# Should show version 17 or higher

echo $JAVA_HOME
# Should show path to Java 17 installation
```

**Pros:**
- ✓ Full client functionality
- ✓ Can create Delta tables from local machine
- ✓ Better for rapid development

**Cons:**
- Requires Java installation
- Larger dependency footprint

---

### Option 3: Use Docker with Mounted Client

Run the Python client inside a Docker container that has Java pre-installed:

```bash
# Create Dockerfile for client
cat > Dockerfile.client <<EOF
FROM openjdk:17-slim

RUN apt-get update && apt-get install -y python3 python3-pip

WORKDIR /app
COPY client/requirements.txt .
RUN pip3 install -r requirements.txt

COPY client/ ./client/
RUN pip3 install -e ./client

CMD ["python3"]
EOF

# Build image
docker build -f Dockerfile.client -t lakehouse-client .

# Run examples
docker run --rm \\
  -v $(pwd)/examples:/examples \\
  -e LAKEHOUSE_HOST=10.16.36.36 \\
  lakehouse-client \\
  python3 /examples/quickstart.py
```

**Pros:**
- ✓ No local Java installation needed
- ✓ Consistent environment
- ✓ Full client functionality

**Cons:**
- Need to use Docker for everything
- More complex setup

---

## Recommended Workflows

### For Development (Local + Remote)

**Install Java 17 locally** and use full `LakehouseClient`:

```python
from lakehouse_client import LakehouseClient

client = LakehouseClient()

# Everything works locally
client.upload_parquet('data.csv', 'raw-data', 'dataset')
client.create_delta_table(...)  # Works!
client.query_to_dataframe(...)
```

### For Production/Remote Deployment

**Use `SimpleLakehouseClient`** and server-side scripts:

```python
from lakehouse_client import SimpleLakehouseClient

client = SimpleLakehouseClient()

# Upload from local machine
s3_uri = client.upload_parquet('data.csv', 'raw-data', 'dataset')

# Create Delta table on server (via script or API)
# Query from local machine
results = client.query_to_dataframe("SELECT * FROM ...")
```

### For CI/CD Pipelines

**Use Docker-based client** for consistent environment:

```yaml
# .github/workflows/data-pipeline.yml
jobs:
  process-data:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run data pipeline
        run: |
          docker run --rm \\
            -v $PWD:/app \\
            -e LAKEHOUSE_HOST=${{ secrets.LAKEHOUSE_HOST }} \\
            lakehouse-client \\
            python3 /app/scripts/process_data.py
```

---

## Troubleshooting

### Check Current Java Version

```bash
java -version
```

### Check JAVA_HOME

```bash
echo $JAVA_HOME
ls -la $JAVA_HOME/bin/java
```

### Multiple Java Versions

If you have multiple Java versions installed:

#### Linux

```bash
# List available versions
sudo update-alternatives --config java

# Set Java 17 as default
sudo update-alternatives --set java /usr/lib/jvm/java-17-openjdk-amd64/bin/java
```

#### macOS (using jEnv)

```bash
# Install jenv
brew install jenv

# Add to shell
echo 'export PATH="$HOME/.jenv/bin:$PATH"' >> ~/.zshrc
echo 'eval "$(jenv init -)"' >> ~/.zshrc

# Add Java versions
jenv add /Library/Java/JavaVirtualMachines/jdk-17.jdk/Contents/Home
jenv add /Library/Java/JavaVirtualMachines/jdk-11.jdk/Contents/Home

# Set global version
jenv global 17.0

# Verify
java -version
```

### PySpark Still Uses Wrong Java

If PySpark still uses the wrong Java version:

```bash
# Explicitly set for PySpark
export PYSPARK_SUBMIT_ARGS="--driver-java-options '-Djava.version=17' pyspark-shell"

# Or unset and reset JAVA_HOME
unset JAVA_HOME
export JAVA_HOME=/path/to/java-17
```

### Still Having Issues?

1. **Completely uninstall old Java versions**:
   ```bash
   # Ubuntu
   sudo apt remove openjdk-11-*

   # macOS
   sudo rm -rf /Library/Java/JavaVirtualMachines/jdk-11.jdk
   ```

2. **Reinstall PySpark**:
   ```bash
   pip uninstall pyspark delta-spark
   pip install pyspark==3.5.0 delta-spark==3.0.0
   ```

3. **Use SimpleLakehouseClient** (no Java needed):
   ```python
   from lakehouse_client import SimpleLakehouseClient
   ```

---

## Summary

| Approach | Java Required? | Best For |
|----------|---------------|----------|
| SimpleLakehouseClient | ❌ No | Remote deployment, production |
| LakehouseClient | ✅ Yes (17+) | Local development, full features |
| Docker Client | ❌ No | CI/CD, consistent environments |

**For your remote server setup (10.16.36.36), we recommend:**
- Use `SimpleLakehouseClient` on your local machine
- Run `server/create_delta_table.py` on the server for Delta operations
- No Java installation needed on your laptop!

See `examples/quickstart_no_java.py` for a working example.
