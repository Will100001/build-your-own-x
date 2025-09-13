const fs = require('fs');
const path = require('path');

/**
 * Android App Builder
 * Creates Android app packages for both VNC Viewer and Server
 */

class AndroidAppBuilder {
    constructor() {
        this.baseDir = path.join(__dirname, '..');
    }

    async buildViewerApp() {
        console.log('Building VNC Viewer for Android...');
        
        // Create Android project structure
        const androidDir = path.join(this.baseDir, 'android', 'viewer');
        this.createDirectory(androidDir);
        
        // Create main directories
        this.createDirectory(path.join(androidDir, 'app', 'src', 'main', 'java', 'com', 'vncproject', 'viewer'));
        this.createDirectory(path.join(androidDir, 'app', 'src', 'main', 'res', 'layout'));
        this.createDirectory(path.join(androidDir, 'app', 'src', 'main', 'res', 'values'));
        this.createDirectory(path.join(androidDir, 'app', 'src', 'main', 'assets', 'www'));
        
        // Copy web assets
        this.copyWebAssets(androidDir, 'viewer');
        
        // Generate Android manifest
        this.generateManifest(androidDir, 'VNC Viewer', 'com.vncproject.viewer');
        
        // Generate MainActivity
        this.generateMainActivity(androidDir, 'viewer');
        
        // Generate build.gradle
        this.generateBuildGradle(androidDir, 'VNC Viewer', 'com.vncproject.viewer');
        
        // Generate strings.xml
        this.generateStringsXml(androidDir, 'VNC Viewer');
        
        // Generate activity_main.xml
        this.generateMainLayout(androidDir);
        
        console.log('VNC Viewer Android app created at:', androidDir);
    }

    async buildServerApp() {
        console.log('Building VNC Server for Android...');
        
        // Create Android project structure
        const androidDir = path.join(this.baseDir, 'android', 'server');
        this.createDirectory(androidDir);
        
        // Create main directories
        this.createDirectory(path.join(androidDir, 'app', 'src', 'main', 'java', 'com', 'vncproject', 'server'));
        this.createDirectory(path.join(androidDir, 'app', 'src', 'main', 'res', 'layout'));
        this.createDirectory(path.join(androidDir, 'app', 'src', 'main', 'res', 'values'));
        this.createDirectory(path.join(androidDir, 'app', 'src', 'main', 'assets', 'www'));
        
        // Copy web assets
        this.copyWebAssets(androidDir, 'server');
        
        // Generate Android manifest
        this.generateManifest(androidDir, 'VNC Server', 'com.vncproject.server');
        
        // Generate MainActivity
        this.generateMainActivity(androidDir, 'server');
        
        // Generate build.gradle
        this.generateBuildGradle(androidDir, 'VNC Server', 'com.vncproject.server');
        
        // Generate strings.xml
        this.generateStringsXml(androidDir, 'VNC Server');
        
        // Generate activity_main.xml
        this.generateMainLayout(androidDir);
        
        console.log('VNC Server Android app created at:', androidDir);
    }

    createDirectory(dir) {
        if (!fs.existsSync(dir)) {
            fs.mkdirSync(dir, { recursive: true });
        }
    }

    copyWebAssets(androidDir, appType) {
        const assetsDir = path.join(androidDir, 'app', 'src', 'main', 'assets', 'www');
        
        // Copy shared assets
        const sharedDir = path.join(this.baseDir, 'shared');
        const sharedFiles = ['vnc-protocol.js', 'vnc-gui.js', 'vnc-styles.css'];
        
        sharedFiles.forEach(file => {
            const source = path.join(sharedDir, file);
            const dest = path.join(assetsDir, file);
            if (fs.existsSync(source)) {
                fs.copyFileSync(source, dest);
            }
        });
        
        // Copy app-specific assets
        const appDir = path.join(this.baseDir, appType);
        const appFile = `${appType}.html`;
        const appJsFile = `${appType}.js`;
        
        if (fs.existsSync(path.join(appDir, appFile))) {
            fs.copyFileSync(
                path.join(appDir, appFile),
                path.join(assetsDir, 'index.html')
            );
        }
        
        if (fs.existsSync(path.join(appDir, appJsFile))) {
            fs.copyFileSync(
                path.join(appDir, appJsFile),
                path.join(assetsDir, `${appType}.js`)
            );
        }
        
        // Create Android-specific index.html
        this.generateAndroidIndexHtml(assetsDir, appType);
    }

    generateAndroidIndexHtml(assetsDir, appType) {
        const htmlContent = `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>VNC ${appType.charAt(0).toUpperCase() + appType.slice(1)}</title>
    <link rel="stylesheet" href="vnc-styles.css">
    <style>
        body {
            margin: 0;
            padding: 0;
            -webkit-user-select: none;
            -webkit-touch-callout: none;
            -webkit-tap-highlight-color: transparent;
        }
        
        .mobile-app {
            height: 100vh;
            display: flex;
            flex-direction: column;
            background: #f5f5f5;
        }
        
        .mobile-header {
            background: #343a40;
            color: white;
            padding: 16px;
            text-align: center;
            font-size: 18px;
            font-weight: 600;
        }
        
        .mobile-content {
            flex: 1;
            overflow: auto;
            padding: 8px;
        }
        
        /* Mobile-specific styles */
        .vnc-viewer,
        .vnc-server {
            margin: 0;
            border-radius: 0;
            box-shadow: none;
            height: 100%;
        }
        
        .toolbar,
        .viewer-controls {
            flex-wrap: wrap;
            padding: 12px;
        }
        
        input[type="text"],
        input[type="number"],
        input[type="password"] {
            width: 100%;
            margin-bottom: 8px;
        }
        
        button {
            min-height: 44px;
            margin: 4px;
        }
        
        .canvas-container {
            min-height: 300px;
        }
        
        #vnc-canvas {
            max-width: 100%;
            height: auto;
        }
        
        /* Touch-friendly controls */
        .mobile-controls {
            background: #f8f9fa;
            padding: 16px;
            border-top: 1px solid #dee2e6;
            display: flex;
            justify-content: space-around;
            gap: 8px;
        }
        
        .mobile-controls button {
            flex: 1;
            min-height: 48px;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="mobile-app">
        <div class="mobile-header">
            VNC ${appType.charAt(0).toUpperCase() + appType.slice(1)}
        </div>
        
        <div class="mobile-content">
            <div id="vnc-app"></div>
        </div>
        
        <div class="mobile-controls">
            ${appType === 'viewer' ? `
            <button onclick="mobileApp.connect()">Connect</button>
            <button onclick="mobileApp.disconnect()">Disconnect</button>
            <button onclick="mobileApp.showKeyboard()">Keyboard</button>
            <button onclick="mobileApp.showMenu()">Menu</button>
            ` : `
            <button onclick="mobileApp.startServer()">Start</button>
            <button onclick="mobileApp.stopServer()">Stop</button>
            <button onclick="mobileApp.shareInfo()">Share</button>
            <button onclick="mobileApp.showSettings()">Settings</button>
            `}
        </div>
    </div>

    <script src="vnc-protocol.js"></script>
    <script src="vnc-gui.js"></script>
    <script src="${appType}.js"></script>
    <script>
        // Mobile app wrapper
        class MobileVNCApp {
            constructor() {
                this.app = null;
                this.appType = '${appType}';
            }
            
            init() {
                // Initialize the appropriate app
                if (this.appType === 'viewer') {
                    this.app = new VNCViewer('vnc-app');
                } else {
                    this.app = new VNCServer('vnc-app');
                }
                
                // Mobile-specific adjustments
                this.setupMobileFeatures();
            }
            
            setupMobileFeatures() {
                // Prevent zoom on double tap
                let lastTouchEnd = 0;
                document.addEventListener('touchend', function (event) {
                    const now = (new Date()).getTime();
                    if (now - lastTouchEnd <= 300) {
                        event.preventDefault();
                    }
                    lastTouchEnd = now;
                }, false);
                
                // Hide address bar on scroll
                window.addEventListener('scroll', function() {
                    if (window.pageYOffset > 0) {
                        window.scrollTo(0, 1);
                    }
                });
            }
            
            connect() {
                if (this.app && this.app.connect) {
                    this.app.connect();
                }
            }
            
            disconnect() {
                if (this.app && this.app.disconnect) {
                    this.app.disconnect();
                }
            }
            
            startServer() {
                if (this.app && this.app.startServer) {
                    this.app.startServer();
                }
            }
            
            stopServer() {
                if (this.app && this.app.stopServer) {
                    this.app.stopServer();
                }
            }
            
            showKeyboard() {
                // Show virtual keyboard
                const input = document.createElement('input');
                input.style.position = 'absolute';
                input.style.left = '-9999px';
                document.body.appendChild(input);
                input.focus();
                setTimeout(() => {
                    document.body.removeChild(input);
                }, 100);
            }
            
            showMenu() {
                alert('Menu functionality would be implemented here');
            }
            
            shareInfo() {
                if (navigator.share) {
                    navigator.share({
                        title: 'VNC Connection',
                        text: 'Connect to my VNC server',
                        url: window.location.href
                    });
                } else {
                    // Fallback
                    alert('Share functionality not available');
                }
            }
            
            showSettings() {
                alert('Settings functionality would be implemented here');
            }
        }
        
        const mobileApp = new MobileVNCApp();
        document.addEventListener('DOMContentLoaded', () => {
            mobileApp.init();
        });
    </script>
</body>
</html>`;
        
        fs.writeFileSync(path.join(assetsDir, 'index.html'), htmlContent);
    }

    generateManifest(androidDir, appName, packageName) {
        const manifestContent = `<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="${packageName}">

    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
    <uses-permission android:name="android.permission.WAKE_LOCK" />
    <uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" />

    <application
        android:allowBackup="true"
        android:icon="@mipmap/ic_launcher"
        android:label="@string/app_name"
        android:theme="@style/AppTheme"
        android:usesCleartextTraffic="true">

        <activity
            android:name=".MainActivity"
            android:exported="true"
            android:screenOrientation="landscape"
            android:configChanges="orientation|screenSize|keyboardHidden">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>`;

        fs.writeFileSync(
            path.join(androidDir, 'app', 'src', 'main', 'AndroidManifest.xml'),
            manifestContent
        );
    }

    generateMainActivity(androidDir, appType) {
        const className = 'MainActivity';
        const packageName = `com.vncproject.${appType}`;
        
        const javaContent = `package ${packageName};

import android.annotation.SuppressLint;
import android.app.Activity;
import android.os.Bundle;
import android.view.View;
import android.view.Window;
import android.view.WindowManager;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

public class ${className} extends Activity {
    private WebView webView;

    @SuppressLint("SetJavaScriptEnabled")
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        
        // Hide title bar and make fullscreen
        requestWindowFeature(Window.FEATURE_NO_TITLE);
        getWindow().setFlags(
            WindowManager.LayoutParams.FLAG_FULLSCREEN,
            WindowManager.LayoutParams.FLAG_FULLSCREEN
        );
        
        // Keep screen on
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        
        setContentView(R.layout.activity_main);
        
        webView = findViewById(R.id.webview);
        setupWebView();
        
        // Load the VNC app
        webView.loadUrl("file:///android_asset/www/index.html");
    }

    private void setupWebView() {
        WebSettings webSettings = webView.getSettings();
        webSettings.setJavaScriptEnabled(true);
        webSettings.setDomStorageEnabled(true);
        webSettings.setAllowFileAccess(true);
        webSettings.setAllowContentAccess(true);
        webSettings.setAllowFileAccessFromFileURLs(true);
        webSettings.setAllowUniversalAccessFromFileURLs(true);
        webSettings.setBuiltInZoomControls(false);
        webSettings.setSupportZoom(false);
        webSettings.setDisplayZoomControls(false);
        webSettings.setUseWideViewPort(true);
        webSettings.setLoadWithOverviewMode(true);
        
        // Enable remote debugging in debug builds
        if (BuildConfig.DEBUG) {
            WebView.setWebContentsDebuggingEnabled(true);
        }
        
        webView.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, String url) {
                view.loadUrl(url);
                return true;
            }
        });
        
        webView.setWebChromeClient(new WebChromeClient());
        
        // Hide system UI for immersive experience
        webView.setSystemUiVisibility(
            View.SYSTEM_UI_FLAG_LAYOUT_STABLE |
            View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION |
            View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN |
            View.SYSTEM_UI_FLAG_HIDE_NAVIGATION |
            View.SYSTEM_UI_FLAG_FULLSCREEN |
            View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
        );
    }

    @Override
    public void onBackPressed() {
        if (webView.canGoBack()) {
            webView.goBack();
        } else {
            super.onBackPressed();
        }
    }

    @Override
    protected void onDestroy() {
        if (webView != null) {
            webView.destroy();
        }
        super.onDestroy();
    }
}`;

        fs.writeFileSync(
            path.join(androidDir, 'app', 'src', 'main', 'java', 'com', 'vncproject', appType, 'MainActivity.java'),
            javaContent
        );
    }

    generateBuildGradle(androidDir, appName, packageName) {
        const gradleContent = `apply plugin: 'com.android.application'

android {
    compileSdkVersion 33
    
    defaultConfig {
        applicationId "${packageName}"
        minSdkVersion 21
        targetSdkVersion 33
        versionCode 1
        versionName "1.0"
    }
    
    buildTypes {
        release {
            minifyEnabled false
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
        }
    }
    
    compileOptions {
        sourceCompatibility JavaVersion.VERSION_1_8
        targetCompatibility JavaVersion.VERSION_1_8
    }
}

dependencies {
    implementation 'androidx.appcompat:appcompat:1.6.1'
    implementation 'androidx.constraintlayout:constraintlayout:2.1.4'
}`;

        fs.writeFileSync(
            path.join(androidDir, 'app', 'build.gradle'),
            gradleContent
        );
    }

    generateStringsXml(androidDir, appName) {
        const stringsContent = `<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">${appName}</string>
</resources>`;

        fs.writeFileSync(
            path.join(androidDir, 'app', 'src', 'main', 'res', 'values', 'strings.xml'),
            stringsContent
        );
    }

    generateMainLayout(androidDir) {
        const layoutContent = `<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:orientation="vertical">

    <WebView
        android:id="@+id/webview"
        android:layout_width="match_parent"
        android:layout_height="match_parent" />

</LinearLayout>`;

        fs.writeFileSync(
            path.join(androidDir, 'app', 'src', 'main', 'res', 'layout', 'activity_main.xml'),
            layoutContent
        );
    }

    async build() {
        console.log('Building Android apps...');
        await this.buildViewerApp();
        await this.buildServerApp();
        console.log('Android apps built successfully!');
    }
}

// Run the builder
if (require.main === module) {
    const builder = new AndroidAppBuilder();
    builder.build().catch(console.error);
}

module.exports = AndroidAppBuilder;