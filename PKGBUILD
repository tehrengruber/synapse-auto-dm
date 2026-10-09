# Maintainer: Ehrengruber Architekten
pkgname=python-synapse-auto-dm
pkgver=0.2.1
pkgrel=1
pkgdesc="Synapse module that automatically creates DM rooms between users, and one room per user with themselves"
arch=('any')
license=('MIT')
depends=('python' 'matrix-synapse>=1.90')
makedepends=('python-build' 'python-installer' 'python-setuptools')
source=()

build() {
    cd "$startdir"
    python -m build --wheel --no-isolation
}

package() {
    cd "$startdir"
    python -m installer --destdir="$pkgdir" dist/*.whl
    install -Dm644 LICENSE "$pkgdir/usr/share/licenses/$pkgname/LICENSE"
}