plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "com.fr8masters.tiyin"
    compileSdk = 36

    defaultConfig {
        applicationId = "com.fr8masters.tiyin"
        minSdk = 26
        targetSdk = 36
        // номер сборки GitHub Actions -> каждая новая сборка выше предыдущей (требование Google Play)
        versionCode = (System.getenv("GITHUB_RUN_NUMBER") ?: "1").toInt() + 100
        versionName = "1.0." + (System.getenv("GITHUB_RUN_NUMBER") ?: "0")
    }

    buildFeatures {
        buildConfig = true
    }

    // lite — без доступа к уведомлениям (Play Protect не блокирует установку), full — с автозаписью пушей
    flavorDimensions += "edition"
    productFlavors {
        create("lite") {
            dimension = "edition"
            buildConfigField("boolean", "AUTO_RECORD", "false")
        }
        create("full") {
            dimension = "edition"
            buildConfigField("boolean", "AUTO_RECORD", "true")
        }
    }

    // Ключ загрузки для Google Play берётся из секретов репозитория (см. .github/workflows/apk.yml)
    val ksFile = System.getenv("TIYIN_KEYSTORE")
    signingConfigs {
        if (ksFile != null && file(ksFile).exists()) {
            create("upload") {
                storeFile = file(ksFile)
                storePassword = System.getenv("TIYIN_KEYSTORE_PASSWORD")
                keyAlias = System.getenv("TIYIN_KEY_ALIAS")
                keyPassword = System.getenv("TIYIN_KEY_PASSWORD")
            }
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            signingConfigs.findByName("upload")?.let { signingConfig = it }
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions {
        jvmTarget = "17"
    }
}

dependencies {
    implementation("androidx.core:core-ktx:1.16.0")
    implementation("androidx.appcompat:appcompat:1.7.0")
    implementation("androidx.swiperefreshlayout:swiperefreshlayout:1.1.0")
}
