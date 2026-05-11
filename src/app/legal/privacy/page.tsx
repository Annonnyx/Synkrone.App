"use client";

import Link from "next/link";
import { ArrowLeft, Shield } from "lucide-react";

export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-[#0a0a0a] text-neutral-50">
      <div className="mx-auto max-w-3xl px-6 py-12">
        <Link href="/" className="mb-8 inline-flex items-center gap-2 text-sm text-neutral-400 transition-colors hover:text-white">
          <ArrowLeft className="h-4 w-4" />
          Retour à l&apos;accueil
        </Link>

        <div className="mb-8 inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-[#00e1ff]/10 text-[#00e1ff] ring-1 ring-white/10">
          <Shield className="h-6 w-6" />
        </div>

        <h1 className="text-3xl font-bold tracking-tight text-white">Politique de confidentialité</h1>
        <p className="mt-2 text-sm text-neutral-500">Dernière mise à jour : 10/05/2026</p>

        <div className="mt-10 space-y-10 text-sm leading-relaxed text-neutral-300">
          <section>
            <h2 className="text-lg font-semibold text-white">Responsable du traitement</h2>
            <p className="mt-2">Synkrone est le responsable du traitement des données collectées sur cette plateforme.</p>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-neutral-400">
              <li>Email : <a href="mailto:contact@synkrone.fr" className="text-[#00e1ff] hover:underline">contact@synkrone.fr</a></li>
              <li>Discord : <a href="https://discord.gg/nuFNvVybGE" target="_blank" rel="noopener noreferrer" className="text-[#00e1ff] hover:underline">Serveur Support</a></li>
            </ul>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-white">Données collectées</h2>
            <div className="mt-4 space-y-4">
              <div>
                <h3 className="font-medium text-white">Données de compte</h3>
                <ul className="mt-1 list-disc space-y-1 pl-5 text-neutral-400">
                  <li>Adresse email</li><li>Nom d&apos;utilisateur</li><li>Mot de passe (chiffré)</li><li>Date d&apos;inscription</li>
                </ul>
              </div>
              <div>
                <h3 className="font-medium text-white">Données de bots</h3>
                <ul className="mt-1 list-disc space-y-1 pl-5 text-neutral-400">
                  <li>Tokens Discord (chiffrés)</li><li>Noms des bots</li><li>Configuration des modules</li><li>Logs d&apos;activité (30 jours)</li>
                </ul>
              </div>
              <div>
                <h3 className="font-medium text-white">Données techniques</h3>
                <ul className="mt-1 list-disc space-y-1 pl-5 text-neutral-400">
                  <li>Adresse IP (anonymisée)</li><li>Type de navigateur</li><li>Cookie de session</li><li>Statistiques d&apos;utilisation</li>
                </ul>
              </div>
              <div>
                <h3 className="font-medium text-white">Données de transaction</h3>
                <ul className="mt-1 list-disc space-y-1 pl-5 text-neutral-400">
                  <li>Historique des achats</li><li>Solde de Krônes</li><li>Factures (10 ans)</li><li>Moyens de paiement (tokenisés)</li>
                </ul>
              </div>
            </div>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-white">Finalités du traitement</h2>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-neutral-400">
              <li><strong className="text-neutral-200">Fourniture du service :</strong> création et gestion de votre compte, fonctionnement des bots</li>
              <li><strong className="text-neutral-200">Sécurité :</strong> protection contre la fraude, authentification, prévention des abus</li>
              <li><strong className="text-neutral-200">Support client :</strong> réponse à vos demandes et résolution de problèmes</li>
              <li><strong className="text-neutral-200">Amélioration :</strong> analyse statistique pour améliorer nos services</li>
              <li><strong className="text-neutral-200">Obligations légales :</strong> conservation des factures, réponse aux autorités</li>
            </ul>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-white">Base légale du traitement</h2>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-neutral-400">
              <li><strong className="text-neutral-200">Exécution du contrat</strong> — nécessaire pour fournir les services demandés (CGU)</li>
              <li><strong className="text-neutral-200">Obligation légale</strong> — conservation des factures, réponse aux réquisitions judiciaires</li>
              <li><strong className="text-neutral-200">Intérêt légitime</strong> — sécurité du service, prévention de la fraude</li>
              <li><strong className="text-neutral-200">Consentement</strong> — cookies non essentiels et communications marketing</li>
            </ul>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-white">Vos droits (RGPD)</h2>
            <p className="mt-2">Conformément au RGPD, vous disposez des droits suivants :</p>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-neutral-400">
              <li><strong className="text-neutral-200">Droit d&apos;accès</strong> — obtenir une copie de vos données</li>
              <li><strong className="text-neutral-200">Droit de rectification</strong> — corriger des données inexactes</li>
              <li><strong className="text-neutral-200">Droit à l&apos;effacement</strong> — demander la suppression</li>
              <li><strong className="text-neutral-200">Droit à la portabilité</strong> — récupérer vos données structurées</li>
              <li><strong className="text-neutral-200">Droit d&apos;opposition</strong> — vous opposer à certains traitements</li>
              <li><strong className="text-neutral-200">Droit de limitation</strong> — restreindre temporairement le traitement</li>
            </ul>
            <p className="mt-2">
              Pour exercer ces droits, contactez-nous à{" "}
              <a href="mailto:privacy@synkrone.fr" className="text-[#00e1ff] hover:underline">privacy@synkrone.fr</a>.
              Nous répondrons dans un délai maximum d&apos;un mois.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-white">Sécurité des données</h2>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-neutral-400">
              <li><strong className="text-neutral-200">Chiffrement :</strong> AES-256 pour les tokens, TLS 1.3 pour les transmissions</li>
              <li><strong className="text-neutral-200">Authentification :</strong> JWT avec expiration, 2FA disponible</li>
              <li><strong className="text-neutral-200">Hébergement :</strong> Serveurs sécurisés en Europe (Hetzner/OVH)</li>
              <li><strong className="text-neutral-200">Backups :</strong> Sauvegardes chiffrées quotidiennes</li>
              <li><strong className="text-neutral-200">Audit :</strong> Tests de sécurité réguliers, monitoring 24/7</li>
            </ul>
            <p className="mt-2">En cas de violation de données, vous serez notifié dans les 72 heures conformément au RGPD.</p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-white">Contact DPO</h2>
            <p className="mt-2">
              <a href="mailto:privacy@synkrone.fr" className="text-[#00e1ff] hover:underline">privacy@synkrone.fr</a>{" "}
              — En cas de litige, vous avez le droit d&apos;introduire une réclamation auprès de la CNIL.
            </p>
          </section>
        </div>
      </div>
    </div>
  );
}
