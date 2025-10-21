# Offline Deployment Guide

This guide explains how to deploy the Lakehouse platform in environments with **no internet access** or **restricted network access** where Docker containers cannot download JARs from Maven repositories.

## Overview

The Lakehouse platform now includes a **custom Spark Docker image** that has all necessary JARs pre-installed:

- **Delta Lake 3.3.0** - Latest version compatible with Spark 3.5
- **Hadoop AWS 3.3.4** - For S3/MinIO connectivity
- **AWS Java SDK Bundle** - Required for S3 operations
- **Additional Hadoop dependencies** - For full S3 support

## Pre-Installed JARs

The custom Spark image includes these JARs bundled at build time:

### Delta Lake (3.3.0)
```
/opt/bitnami/spark/jars/delta-spark_2.12-3.3.0.jar
/opt/bitnami/spark/jars/delta-storage-3.3.0.jar
```

### S3/MinIO Support
```
/opt/bitnami/spark/jars/hadoop-aws-3.3.4.jar
/opt/bitnami/spark/jars/aws-java-sdk-bundle-1.12.367.jar
/opt/bitnami/spark/jars/hadoop-common-3.3.4.jar
/opt/bitnami/spark/jars/hadoop-auth-3.3.4.jar
```

### Additional Dependencies
```
/opt/bitnami/spark/jars/commons-configuration2-2.8.0.jar
/opt/bitnami/spark/jars/commons-logging-1.2.jar
```

## Building the Custom Image

### Prerequisites

- Docker installed on the build machine
- Internet access on the build machine (to download JARs)
- Sufficient disk space (~2GB)

### Build Steps

#### 1. On a Machine with Internet Access

```bash
cd lakehouse

# Build the custom Spark image
docker-compose build spark-master

# This will:
# - Download all JARs from Maven Central
# - Bundle them into the Docker image
# - Tag as lakehouse-spark:3.5.0-delta3.3.0
```

The build process:
1. Extends `bitnami/spark:3.5.0`
2. Downloads all required JARs from Maven Central
3. Places JARs in `/opt/bitnami/spark/jars/`
4. Sets proper permissions

#### 2. Verify the Build

```bash
# Check image was created
docker images | grep lakehouse-spark

# Should show:
# lakehouse-spark    3.5.0-delta3.3.0    <image-id>    <size>    <time>

# Verify JARs are present
docker run --rm lakehouse-spark:3.5.0-delta3.3.0 \
  ls -lh /opt/bitnami/spark/jars/ | grep -E "(delta|hadoop-aws)"
```

Expected output:
```
-rw-r--r-- 1 1001 1001  28M delta-spark_2.12-3.3.0.jar
-rw-r--r-- 1 1001 1001 156K delta-storage-3.3.0.jar
-rw-r--r-- 1 1001 1001 283M aws-java-sdk-bundle-1.12.367.jar
-rw-r--r-- 1 1001 1001 811K hadoop-aws-3.3.4.jar
```

#### 3. Save the Image for Transfer

For offline deployment on a remote server:

```bash
# Save the custom Spark image to a tar file
docker save lakehouse-spark:3.5.0-delta3.3.0 -o lakehouse-spark-delta.tar

# Compress for transfer (optional but recommended)
gzip lakehouse-spark-delta.tar

# File size will be approximately 1.5-2GB
ls -lh lakehouse-spark-delta.tar.gz
```

#### 4. Transfer to Offline Server

```bash
# Copy to remote server (10.16.36.36)
scp lakehouse-spark-delta.tar.gz user@10.16.36.36:/tmp/

# Or use USB drive, internal file transfer, etc.
```

#### 5. Load Image on Offline Server

```bash
# SSH to the offline server
ssh user@10.16.36.36

# Load the image
gunzip /tmp/lakehouse-spark-delta.tar.gz
docker load -i /tmp/lakehouse-spark-delta.tar

# Verify
docker images | grep lakehouse-spark
```

#### 6. Start Services

```bash
cd /path/to/lakehouse

# Services will use the pre-built image
docker-compose up -d
```

## How It Works

### Without Custom Image (Online)

```
spark-submit --packages io.delta:delta-core_2.12:3.3.0 script.py
                   ↓
         Downloads JARs from Maven Central
                   ↓
              ✗ FAILS in offline environment
```

### With Custom Image (Offline)

```
spark-submit script.py
       ↓
JARs already in /opt/bitnami/spark/jars/
       ↓
   ✓ WORKS offline!
```

## Docker Compose Configuration

The `docker-compose.yml` is configured to build the custom image:

```yaml
spark-master:
  build:
    context: ./docker/spark
    dockerfile: Dockerfile
  image: lakehouse-spark:3.5.0-delta3.3.0
  # ... rest of config
```

### For Pre-Built Image

If you've already built and saved the image, you can skip the build step:

```yaml
spark-master:
  image: lakehouse-spark:3.5.0-delta3.3.0  # Use pre-loaded image
  # Remove 'build' section
```

## Verification

### Check JARs in Running Container

```bash
# List all Delta Lake JARs
docker exec lakehouse-spark-master \
  ls -lh /opt/bitnami/spark/jars/ | grep delta

# List all Hadoop AWS JARs
docker exec lakehouse-spark-master \
  ls -lh /opt/bitnami/spark/jars/ | grep hadoop-aws

# Count total JARs
docker exec lakehouse-spark-master \
  ls /opt/bitnami/spark/jars/ | wc -l
```

### Test Delta Lake Functionality

```bash
# On the server, test Delta Lake
python server/create_delta_table.py \
  s3a://raw-data/test.parquet \
  main \
  default \
  test_table

# Should complete without downloading anything
```

### Check Spark Logs

```bash
# Look for JAR loading messages
docker logs lakehouse-spark-master 2>&1 | grep -i delta

# Should see Delta Lake classes being loaded
```

## Troubleshooting

### ClassNotFoundException

**Error:**
```
java.lang.ClassNotFoundException: io.delta.sql.DeltaSparkSessionExtension
```

**Solution:**
```bash
# Verify JARs are present
docker exec lakehouse-spark-master ls /opt/bitnami/spark/jars/delta*

# If missing, rebuild the image
docker-compose build --no-cache spark-master
```

### Cannot Download JARs During Build

**Error:**
```
wget: unable to resolve host address 'repo1.maven.org'
```

**Solution:**
- Build the image on a machine with internet access
- Save and transfer the built image (see step 3 above)

### Image Size Too Large

The custom image is larger (~2GB) due to bundled JARs.

**Options:**
1. **Accept the size** - This is normal for a full Spark + Delta Lake image
2. **Remove unused JARs** - Edit `docker/spark/Dockerfile` to exclude JARs you don't need
3. **Use compression** - Always use `gzip` when transferring

## Updating Delta Lake Version

To use a different Delta Lake version:

### 1. Edit the Dockerfile

```dockerfile
# In docker/spark/Dockerfile

# Change this line:
RUN wget https://repo1.maven.org/maven2/io/delta/delta-spark_2.12/3.3.0/delta-spark_2.12-3.3.0.jar

# To new version:
RUN wget https://repo1.maven.org/maven2/io/delta/delta-spark_2.12/3.4.0/delta-spark_2.12-3.4.0.jar
```

### 2. Update All Version References

```dockerfile
# Update delta-storage version too
RUN wget https://repo1.maven.org/maven2/io/delta/delta-storage/3.4.0/delta-storage-3.4.0.jar
```

### 3. Update Python Client

```python
# In client/requirements.txt
delta-spark==3.4.0  # Match the Dockerfile version
```

### 4. Rebuild

```bash
docker-compose build --no-cache spark-master
```

## Compatibility Matrix

| Component | Version | Notes |
|-----------|---------|-------|
| Spark | 3.5.0 | Base image from Bitnami |
| Delta Lake | 3.3.0 | Latest compatible with Spark 3.5 |
| Scala | 2.12 | Required for Spark 3.5 |
| Hadoop | 3.3.4 | For S3 support |
| Java | 17 | Required by Spark 3.5 |
| Python Delta | 3.3.0 | Must match server-side version |

## Best Practices

### 1. Version Pinning

Always pin exact versions to ensure consistency:

```
delta-spark==3.3.0  ✓ (exact version)
delta-spark>=3.0.0  ✗ (may cause mismatches)
```

### 2. Pre-Build Images

- Build images on a dedicated build machine with internet
- Test thoroughly before deploying to production
- Keep built images in a private registry or file server

### 3. Documentation

- Document which JAR versions are bundled
- Keep track of build dates
- Note any custom modifications

### 4. Testing

Before deploying to offline environment:
```bash
# Test in isolated network (no internet)
docker network create isolated
docker run --network isolated lakehouse-spark:3.5.0-delta3.3.0 \
  spark-submit --version
```

## Alternative: Private Maven Repository

For large deployments, consider hosting a private Maven repository:

1. **Nexus or Artifactory** - Host JARs internally
2. **Update Dockerfile** - Point to private repo
3. **Cached Downloads** - Faster builds, version control

## Summary

✅ All JARs are pre-downloaded and bundled in Docker image
✅ No internet required on deployment server
✅ No Maven/Ivy downloads during Spark jobs
✅ Consistent versions across all environments
✅ Single image build, deploy anywhere

The custom Spark image ensures the Lakehouse platform works in completely offline environments without any external dependencies.
