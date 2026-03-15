# Maintainer: Ehrengruber Architekten
pkgname=python-synapse-auto-dm
pkgver=0.1.0
pkgrel=1
pkgdesc="Synapse module that automatically creates DM rooms between users on registration"
arch=('any')
license=('custom')
depends=('python' 'matrix-synapse')
makedepends=('python-build' 'python-installer' 'python-setuptools')
source=()

build() {
    cd "$startdir"
    python -m build --wheel --no-isolation
}

package() {
    cd "$startdir"
    python -m installer --destdir="$pkgdir" dist/*.whl
}