# Custom Spark Docker Image

This directory contains a custom Dockerfile that extends the official Bitnami Spark image with pre-installed Delta Lake and S3 dependencies.

## Purpose

The custom image ensures all necessary JARs are bundled at build time, eliminating the need for:
- Maven/Ivy downloads during runtime
- Internet connectivity on deployment servers
- `--packages` flags in spark-submit commands

## What's Included

### Delta Lake 3.3.0
- `delta-spark_2.12-3.3.0.jar` - Main Delta Lake Spark integration
- `delta-storage-3.3.0.jar` - Delta Lake storage layer

### S3/MinIO Support
- `hadoop-aws-3.3.4.jar` - Hadoop AWS connector for S3
- `aws-java-sdk-bundle-1.12.367.jar` - AWS SDK for Java
- `hadoop-common-3.3.4.jar` - Hadoop common utilities
- `hadoop-auth-3.3.4.jar` - Hadoop authentication

### Additional Dependencies
- `commons-configuration2-2.8.0.jar` - Apache Commons Configuration
- `commons-logging-1.2.jar` - Apache Commons Logging

## Building the Image

### Local Build

```bash
# From the lakehouse root directory
docker-compose build spark-master

# Or build directly
cd docker/spark
docker build -t lakehouse-spark:3.5.0-delta3.3.0 .
```

### Build Output

The build process:
1. Pulls base image: `bitnami/spark:3.5.0`
2. Installs `wget` for downloading JARs
3. Downloads all JARs from Maven Central
4. Copies JARs to `/opt/bitnami/spark/jars/`
5. Sets proper permissions for user `1001`

### Verify Build

```bash
# Check image exists
docker images | grep lakehouse-spark

# List bundled JARs
docker run --rm lakehouse-spark:3.5.0-delta3.3.0 \
  ls -lh /opt/bitnami/spark/jars/ | grep -E "(delta|hadoop)"
```

## Image Details

- **Base Image**: `bitnami/spark:3.5.0`
- **Spark Version**: 3.5.0
- **Scala Version**: 2.12
- **Java Version**: 17 (from base image)
- **Delta Lake Version**: 3.3.0
- **Image Size**: ~2GB (with all JARs)

## Offline Deployment

For deployment to servers without internet access:

```bash
# Save image
docker save lakehouse-spark:3.5.0-delta3.3.0 | gzip > lakehouse-spark.tar.gz

# Transfer to offline server
scp lakehouse-spark.tar.gz user@server:/tmp/

# Load on offline server
ssh user@server
gunzip < /tmp/lakehouse-spark.tar.gz | docker load
```

## Customization

### Adding More JARs

Edit the Dockerfile to download additional JARs:

```dockerfile
# Add after existing RUN commands
RUN wget https://repo1.maven.org/maven2/groupId/artifactId/version/artifact.jar
```

### Using Different Versions

To use a different Delta Lake version:

```dockerfile
# Change version in wget URLs
RUN wget https://repo1.maven.org/maven2/io/delta/delta-spark_2.12/3.4.0/delta-spark_2.12-3.4.0.jar
```

**Important**: Also update `client/requirements.txt` to match:
```
delta-spark==3.4.0
```

### Optimizing Image Size

To reduce image size:

```dockerfile
# Remove wget after downloading JARs
RUN apt-get update && apt-get install -y wget && \
    # ... download JARs ... && \
    apt-get remove -y wget && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*
```

## JAR Locations

JARs are placed in two locations:

1. **Primary**: `/opt/bitnami/spark/jars/`
   - Automatically loaded by Spark
   - Used by all Spark jobs

2. **Backup**: `/opt/bitnami/spark/jars-custom/`
   - Original download location
   - Can be used for troubleshooting

## Environment Variables

The image sets:

```dockerfile
ENV SPARK_EXTRA_CLASSPATH=/opt/bitnami/spark/jars-custom/*:$SPARK_EXTRA_CLASSPATH
```

This ensures custom JARs are always on the classpath.

## Troubleshooting

### JARs Not Found

```bash
# Check JARs are present
docker exec lakehouse-spark-master ls /opt/bitnami/spark/jars/ | grep delta

# If missing, rebuild
docker-compose build --no-cache spark-master
```

### Build Fails - Cannot Download

**Error**: `wget: unable to resolve host`

**Solution**: Build on a machine with internet access, then transfer the image.

### Permission Issues

**Error**: `Permission denied accessing JAR files`

**Solution**: JARs should be owned by user `1001`. Rebuild if permissions are wrong:

```bash
docker-compose build --no-cache spark-master
```

### Wrong Java Version

The base image includes Java 17. If you need a different version:

```dockerfile
# In Dockerfile, before USER 1001
RUN apt-get update && \
    apt-get install -y openjdk-17-jdk && \
    rm -rf /var/lib/apt/lists/*
```

## Version Compatibility

| Spark | Delta Lake | Scala | Java |
|-------|-----------|-------|------|
| 3.5.x | 3.3.x     | 2.12  | 17+  |
| 3.4.x | 3.0.x     | 2.12  | 11+  |
| 3.3.x | 2.4.x     | 2.12  | 11+  |

**Current Configuration**: Spark 3.5.0 + Delta Lake 3.3.0 + Scala 2.12 + Java 17

## Testing

### Test Delta Lake Integration

```bash
# Start container
docker run --rm -it lakehouse-spark:3.5.0-delta3.3.0 bash

# Inside container, test Spark with Delta
spark-shell --conf spark.sql.extensions=io.delta.sql.DeltaSparkSessionExtension

# Should start without downloading anything
```

### Test S3 Connectivity

```python
# Create test script
cat > test_s3.py <<EOF
from pyspark.sql import SparkSession

spark = SparkSession.builder \\
    .config("spark.hadoop.fs.s3a.endpoint", "http://minio:9000") \\
    .config("spark.hadoop.fs.s3a.access.key", "minioadmin") \\
    .config("spark.hadoop.fs.s3a.secret.key", "minioadmin") \\
    .getOrCreate()

# Test S3 access
df = spark.read.parquet("s3a://bucket/file.parquet")
df.show()
EOF

# Run test
docker exec lakehouse-spark-master spark-submit test_s3.py
```

## Maintenance

### Updating Dependencies

1. Check for new versions at [Maven Central](https://search.maven.org/)
2. Update version numbers in Dockerfile
3. Update `client/requirements.txt` to match
4. Rebuild and test
5. Document changes in CHANGELOG

### Monitoring Image Size

```bash
# Check layer sizes
docker history lakehouse-spark:3.5.0-delta3.3.0

# Find large layers
docker history lakehouse-spark:3.5.0-delta3.3.0 --format "{{.Size}}\t{{.CreatedBy}}" | sort -h
```

## Resources

- [Bitnami Spark GitHub](https://github.com/bitnami/containers/tree/main/bitnami/spark)
- [Delta Lake Documentation](https://docs.delta.io/)
- [Hadoop AWS Documentation](https://hadoop.apache.org/docs/stable/hadoop-aws/tools/hadoop-aws/index.html)
- [Maven Central Repository](https://repo1.maven.org/maven2/)

## Support

For issues with the custom image:
1. Check this README
2. Review [OFFLINE_DEPLOYMENT.md](../../OFFLINE_DEPLOYMENT.md)
3. Check Docker build logs: `docker-compose build spark-master`
4. Verify base image is up to date: `docker pull bitnami/spark:3.5.0`
