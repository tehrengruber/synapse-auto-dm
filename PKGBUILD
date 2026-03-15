# Maintainer: Ehrengruber Architekten
pkgname=python-synapse-auto-dm
pkgver=0.1.0
pkgrel=1
pkgdesc="Synapse module that automatically creates DM rooms between users on registration"
arch=('any')
license=('custom')
depends=('python' 'matrix-synapse')
makedepends=('python-build' 'python-installer' 'python-setuptools')
source=("git+https://github.com/ehrengruber-architekten/ea-element-web.git")
sha256sums=('SKIP')

pkgver() {
    cd "ea-element-web"
    printf "r%s.%s" "$(git rev-list --count HEAD)" "$(git rev-parse --short HEAD)"
}

build() {
    cd "ea-element-web/synapse_auto_dm"
    python -m build --wheel --no-isolation
}

package() {
    cd "ea-element-web/synapse_auto_dm"
    python -m installer --destdir="$pkgdir" dist/*.whl
}